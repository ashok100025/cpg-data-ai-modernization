"""Weekly revenue and demand forecast with a time-based backtest.

What:   net_revenue and net_units, per category (as-is) x region (as-is), weekly, 8 weeks ahead.
Input:  metrics come ONLY from the metric compiler (metrics/metrics.yml) - same definitions as reporting.
Models: seasonal_naive        y_hat(t) = y(t-52)                            -> the baseline to beat
        seasonal_naive_trend  y_hat(t) = y(t-52) * r                        -> r = last 8 weeks vs the same
                                                                               8 weeks a year earlier, clipped
Validation: rolling-origin backtest over the last 4 months; WAPE, bias and forecast value added (FVA)
            vs the baseline. The model with the lowest backtest WAPE per measure is selected.

Leakage guard: every forecast function receives ONLY the history before its origin (an array slice),
so it cannot see the future by construction; tests/test_forecast.py proves it.

Per-series confidence: overall WAPE is dominated by large series, so accuracy is also scored per
series and labelled high (<20%), medium (20-35%) or low (>35%); consumers see the label next to the number.

Writes gold.forecast_backtest, gold.forecast_accuracy, gold.forecast_series_accuracy, gold.forecast_weekly.
Run:  make forecast
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.poc.metrics import MetricCatalog  # noqa: E402

DB = Path("data/warehouse/cpg.duckdb")
MEASURES = ["net_revenue", "net_units"]
SERIES_DIMS = ["category_as_is", "region_as_is"]   # as-is: future sales happen in today's region/category
HORIZON = 8
SEASON = 52
TREND_WINDOW = 8
TREND_CLIP = (0.5, 2.0)
BACKTEST_ORIGINS_FROM_END = [16, 13, 10, 7]       # origins (weeks before the last week) -> last ~4 months


# ---------------- models: each sees only `history` (weeks before the origin) ----------------
def seasonal_naive(history: np.ndarray, horizon: int) -> np.ndarray:
    n = len(history)
    if n < SEASON:
        raise ValueError("need at least one year of history")
    return np.array([history[n - SEASON + h] if h < SEASON else np.nan for h in range(horizon)], dtype=float)


def seasonal_naive_trend(history: np.ndarray, horizon: int) -> np.ndarray:
    n = len(history)
    if n < SEASON + TREND_WINDOW:
        raise ValueError("need one year plus the trend window of history")
    recent = history[n - TREND_WINDOW:].sum()
    year_ago = history[n - SEASON - TREND_WINDOW:n - SEASON].sum()
    ratio = 1.0 if year_ago == 0 else float(np.clip(recent / year_ago, *TREND_CLIP))
    return seasonal_naive(history, horizon) * ratio


MODELS = {"seasonal_naive": seasonal_naive, "seasonal_naive_trend": seasonal_naive_trend}


def wape(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Weighted absolute percentage error: total absolute error / total actual. Robust to small series."""
    denom = np.abs(actual).sum()
    return float(np.abs(actual - forecast).sum() / denom) if denom else float("nan")


def bias(actual: np.ndarray, forecast: np.ndarray) -> float:
    """Positive = over-forecast, negative = under-forecast, as a share of actuals."""
    denom = np.abs(actual).sum()
    return float((forecast - actual).sum() / denom) if denom else float("nan")


# ---------------- data ----------------
def load_weekly(con) -> tuple[pd.DataFrame, pd.Timestamp]:
    q = MetricCatalog.load().compile(metrics=MEASURES, dimensions=["week"] + SERIES_DIMS)
    df = con.execute(q.sql, q.params).df()
    df["week"] = pd.to_datetime(df["week"])
    max_day = pd.Timestamp(con.sql("select max(event_date_local) from gold.fct_sales_line").fetchone()[0])
    last_full_week = (max_day - pd.Timedelta(days=6)).to_period("W-SUN").start_time
    if (last_full_week + pd.Timedelta(days=6)) > max_day:
        last_full_week -= pd.Timedelta(weeks=1)
    df = df[df["week"] <= last_full_week]          # never learn from or score a partial week
    return df, last_full_week


def to_matrix(df: pd.DataFrame, measure: str) -> pd.DataFrame:
    """weeks x series matrix; weeks with no sales for a series are real zeros."""
    m = df.pivot_table(index="week", columns=SERIES_DIMS, values=measure, aggfunc="sum")
    full = pd.date_range(m.index.min(), m.index.max(), freq="W-MON")
    return m.reindex(full).fillna(0).astype(float)


# ---------------- backtest + forecast ----------------
def run(con) -> dict:
    df, last_week = load_weekly(con)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bt_rows, fc_rows = [], []
    for measure in MEASURES:
        mat = to_matrix(df, measure)
        weeks, values = mat.index, mat.to_numpy()
        n = len(weeks)
        for back in BACKTEST_ORIGINS_FROM_END:
            origin = n - back                         # first forecast week index
            for model_name, fn in MODELS.items():
                for j, series in enumerate(mat.columns):
                    fc = fn(values[:origin, j], HORIZON)        # <- only the past is passed in
                    for h in range(HORIZON):
                        t = origin + h
                        if t >= n:
                            break
                        bt_rows.append(dict(measure=measure, model=model_name, origin_week=weeks[origin].date(),
                                            week=weeks[t].date(), horizon=h + 1, category=series[0], region=series[1],
                                            actual=values[t, j], forecast=fc[h]))
        # final forecast from the end of history, all models (selection flag added below)
        future_weeks = [weeks[-1] + pd.Timedelta(weeks=h + 1) for h in range(HORIZON)]
        for model_name, fn in MODELS.items():
            for j, series in enumerate(mat.columns):
                fc = fn(values[:, j], HORIZON)
                for h in range(HORIZON):
                    fc_rows.append(dict(run_id=run_id, as_of_week=weeks[-1].date(), measure=measure, model=model_name,
                                        week=future_weeks[h].date(), horizon=h + 1, category=series[0],
                                        region=series[1], forecast=fc[h]))

    bt = pd.DataFrame(bt_rows)
    acc = (bt.groupby(["measure", "model"])
             .apply(lambda g: pd.Series({"wape": wape(g.actual.to_numpy(), g.forecast.to_numpy()),
                                         "bias": bias(g.actual.to_numpy(), g.forecast.to_numpy()),
                                         "points": len(g)}), include_groups=False)
             .reset_index())
    base = acc[acc.model == "seasonal_naive"].set_index("measure")["wape"]
    acc["fva_vs_naive"] = 1 - acc["wape"] / acc["measure"].map(base)
    best = acc.loc[acc.groupby("measure")["wape"].idxmin()].set_index("measure")["model"]
    acc["is_selected"] = acc.apply(lambda r: best[r.measure] == r.model, axis=1)

    sel = bt[bt.apply(lambda r: best[r.measure] == r.model, axis=1)]
    ser = (sel.groupby(["measure", "category", "region"])
              .apply(lambda g: pd.Series({"wape": wape(g.actual.to_numpy(), g.forecast.to_numpy()),
                                          "bias": bias(g.actual.to_numpy(), g.forecast.to_numpy()),
                                          "backtest_actual": g.actual.sum()}), include_groups=False)
              .reset_index())
    ser["confidence"] = pd.cut(ser["wape"], [-np.inf, 0.20, 0.35, np.inf], labels=["high", "medium", "low"]).astype(str)

    fc = pd.DataFrame(fc_rows)
    fc["is_selected"] = fc.apply(lambda r: best[r.measure] == r.model, axis=1)
    fc = fc.merge(ser[["measure", "category", "region", "confidence"]], on=["measure", "category", "region"], how="left")

    for name, frame in [("forecast_backtest", bt), ("forecast_accuracy", acc),
                        ("forecast_series_accuracy", ser), ("forecast_weekly", fc)]:
        con.register("_frame", frame)
        con.execute(f"create or replace table gold.{name} as select * from _frame")
        con.unregister("_frame")
    return dict(last_week=last_week.date(), accuracy=acc, series_accuracy=ser, series=len(to_matrix(df, MEASURES[0]).columns),
                weeks=len(to_matrix(df, MEASURES[0])), run_id=run_id)


def main() -> int:
    if not DB.exists():
        sys.exit(f"{DB} not found - run `make build` first.")
    con = duckdb.connect(str(DB))
    out = run(con)
    print(f"Forecast run {out['run_id']}: {out['series']} series (category x region, as-is), "
          f"{out['weeks']} weeks of history up to week starting {out['last_week']}, horizon {HORIZON} weeks")
    print("\nBacktest accuracy (4 origins over the last ~4 months, horizons 1-8):")
    a = out["accuracy"].copy()
    for _, r in a.sort_values(["measure", "wape"]).iterrows():
        mark = "  <- selected" if r.is_selected else ""
        print(f"  {r.measure:12} {r.model:22} WAPE {r.wape:6.1%}   bias {r.bias:+6.1%}   "
              f"FVA vs naive {r.fva_vs_naive:+6.1%}{mark}")
    sa = out["series_accuracy"]
    for m in MEASURES:
        counts = sa[sa.measure == m]["confidence"].value_counts().to_dict()
        low = sa[(sa.measure == m) & (sa.confidence == "low")]
        print(f"\n  {m}: series confidence high={counts.get('high', 0)} medium={counts.get('medium', 0)} "
              f"low={counts.get('low', 0)}" + (f"  (low: {', '.join(low.category + '/' + low.region)})" if len(low) else ""))
    print("\nTables: gold.forecast_backtest, gold.forecast_accuracy, gold.forecast_series_accuracy, gold.forecast_weekly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
