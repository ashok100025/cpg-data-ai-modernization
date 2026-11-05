"""Forecast: models behave as specified, metrics are right, and no future data can leak in."""
import numpy as np
import pandas as pd
import pytest

from src.poc import forecast as fc


def test_seasonal_naive_repeats_last_year():
    history = np.arange(60, dtype=float)                 # week i has value i
    assert list(fc.seasonal_naive(history, 3)) == [8.0, 9.0, 10.0]   # weeks 60..62 -> values of 8..10


def test_trend_model_scales_by_recent_growth():
    year1 = np.full(52, 100.0)
    history = np.concatenate([year1, np.full(16, 110.0)])     # +10% vs a year ago
    out = fc.seasonal_naive_trend(history, 4)
    assert out == pytest.approx([110.0] * 4)


def test_trend_ratio_is_clipped():
    history = np.concatenate([np.full(52, 1.0), np.full(16, 100.0)])
    assert max(fc.seasonal_naive_trend(history, 1)) == pytest.approx(1.0 * fc.TREND_CLIP[1])


def test_models_refuse_short_history():
    with pytest.raises(ValueError):
        fc.seasonal_naive(np.ones(10), 4)


def test_wape_and_bias():
    a, f = np.array([100.0, 100.0]), np.array([90.0, 130.0])
    assert fc.wape(a, f) == pytest.approx(0.2)
    assert fc.bias(a, f) == pytest.approx(0.1)


@pytest.mark.parametrize("model", list(fc.MODELS))
def test_no_leakage_future_values_cannot_change_a_forecast(model):
    """Changing every value at or after the origin must not change the forecast made at the origin."""
    rng = np.random.default_rng(0)
    series = rng.uniform(50, 150, 90)
    origin = 70
    tampered = series.copy()
    tampered[origin:] = 1e9
    fn = fc.MODELS[model]
    assert np.array_equal(fn(series[:origin], 8), fn(tampered[:origin], 8))


def test_backtest_never_scores_before_origin_and_uses_full_weeks(con):
    bt = con.sql("select origin_week, week, horizon from gold.forecast_backtest").df()
    assert (bt.week >= bt.origin_week).all()
    assert ((bt.week - bt.origin_week).dt.days == (bt.horizon - 1) * 7).all()
    last_full = con.sql("select max(week) from gold.forecast_backtest").fetchone()[0]
    max_day = con.sql("select max(event_date_local) from gold.fct_sales_line").fetchone()[0]
    assert (max_day - last_full).days >= 6                      # the last scored week is complete


def test_selected_model_beats_baseline_and_every_forecast_has_confidence(con):
    acc = con.sql("select measure, model, wape, is_selected from gold.forecast_accuracy").df()
    for m, g in acc.groupby("measure"):
        sel = g[g.is_selected].iloc[0]
        assert sel.wape <= g[g.model == "seasonal_naive"].wape.iloc[0], m
    missing = con.sql("select count(*) from gold.forecast_weekly where is_selected and confidence is null").fetchone()[0]
    assert missing == 0


def test_stored_backtest_used_only_data_before_each_origin(con):
    """Independently re-forecast every stored backtest point from weeks strictly before its origin.
    Catches a leak in the backtest loop itself (e.g. passing one extra week), not just in the models."""
    df, _ = fc.load_weekly(con)
    bt = con.sql("select measure, model, origin_week, horizon, category, region, forecast "
                 "from gold.forecast_backtest").df()
    for measure in fc.MEASURES:
        mat = fc.to_matrix(df, measure)
        week_index = {pd.Timestamp(w): i for i, w in enumerate(mat.index)}
        cols = {c: j for j, c in enumerate(mat.columns)}
        values = mat.to_numpy()
        sub = bt[bt.measure == measure]
        for (model, origin, cat, reg), g in sub.groupby(["model", "origin_week", "category", "region"]):
            o = week_index[pd.Timestamp(origin)]
            expected = fc.MODELS[model](values[:o, cols[(cat, reg)]], fc.HORIZON)
            got = g.sort_values("horizon").forecast.to_numpy()
            assert np.allclose(got, expected[:len(got)]), (measure, model, origin, cat, reg)
