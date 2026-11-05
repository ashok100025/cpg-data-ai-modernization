"""Metric compiler - the only code allowed to turn metric names into SQL.

    from src.poc.metrics import MetricCatalog
    cat = MetricCatalog.load()
    q = cat.compile(metrics=["net_revenue", "return_rate"], dimensions=["week", "region"],
                    filters={"category": ["Snacks"]}, date_from="2026-01-01", date_to="2026-06-30")
    rows = duckdb_connection.execute(q.sql, q.params).fetchall()

Guarantees:
  * unknown metrics, dimensions or filters are refused (MetricError) - nothing is guessed
  * filter values are always bound parameters, never pasted into SQL
  * ratio metrics are computed from their base metrics' definitions, so they cannot drift
  * a join is added only when a requested dimension needs it (no accidental fan-out)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CATALOG_PATH = Path(__file__).resolve().parents[2] / "metrics" / "metrics.yml"
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class MetricError(ValueError):
    """Raised when a request asks for something the catalogue does not define or allow."""


@dataclass
class CompiledQuery:
    sql: str
    params: list
    metrics: list[str]
    dimensions: list[str]
    metadata: dict = field(default_factory=dict)   # per-metric owner / unit / sensitivity, for traceability


class MetricCatalog:
    def __init__(self, spec: dict):
        self.spec = spec
        self.metrics: dict = spec["metrics"]
        self.dimensions: dict = spec["dimensions"]
        self.joins: dict = spec["source"]["joins"]
        self.fact: str = spec["source"]["fact"]
        self.date_column: str = spec["source"]["date_column"]
        self._validate()

    @classmethod
    def load(cls, path: Path | str = CATALOG_PATH) -> "MetricCatalog":
        with open(path) as f:
            return cls(yaml.safe_load(f))

    # ---------- catalogue integrity ----------
    def _validate(self) -> None:
        for name, m in self.metrics.items():
            for key in ("description", "owner", "sensitivity", "unit"):
                if key not in m:
                    raise MetricError(f"metric {name!r} is missing {key!r}")
            if m["sensitivity"] not in self.spec["sensitivity_levels"]:
                raise MetricError(f"metric {name!r} has unknown sensitivity {m['sensitivity']!r}")
            if m.get("type") == "ratio":
                for part in ("numerator", "denominator"):
                    base = self.metrics.get(m.get(part))
                    if base is None or base.get("type") == "ratio":
                        raise MetricError(f"ratio {name!r}: {part} must be a simple metric")
            elif "expr" not in m:
                raise MetricError(f"metric {name!r} has no expr")
        for name, d in self.dimensions.items():
            if d.get("join") and d["join"] not in self.joins:
                raise MetricError(f"dimension {name!r} uses unknown join {d['join']!r}")

    # ---------- compilation ----------
    def metric_expr(self, name: str) -> str:
        m = self.metrics[name]
        if m.get("type") == "ratio":
            num = self.metrics[m["numerator"]]["expr"]
            den = self.metrics[m["denominator"]]["expr"]
            return f"({num}) / nullif({den}, 0)"
        return m["expr"]

    def compile(self, metrics: list[str], dimensions: list[str] | None = None,
                filters: dict[str, list | str] | None = None,
                date_from: str | None = None, date_to: str | None = None,
                order_by_dimensions: bool = True) -> CompiledQuery:
        dimensions = list(dimensions or [])
        filters = dict(filters or {})
        if not metrics:
            raise MetricError("at least one metric is required")
        unknown = [m for m in metrics if m not in self.metrics]
        if unknown:
            raise MetricError(f"unknown metric(s): {unknown}. Known: {sorted(self.metrics)}")
        bad_dims = [d for d in dimensions + list(filters) if d not in self.dimensions]
        if bad_dims:
            raise MetricError(f"unknown dimension(s): {bad_dims}. Known: {sorted(self.dimensions)}")
        if len(set(dimensions)) != len(dimensions):
            raise MetricError("duplicate dimensions")
        for d in (date_from, date_to):
            if d is not None and not _DATE.match(str(d)):
                raise MetricError(f"dates must be YYYY-MM-DD, got {d!r}")

        joins_needed = []
        for d in dimensions + list(filters):
            j = self.dimensions[d].get("join")
            if j and j not in joins_needed:
                joins_needed.append(j)

        select = [f"{self.dimensions[d]['expr']} as {d}" for d in dimensions]
        select += [f"{self.metric_expr(m)} as {m}" for m in metrics]
        sql = ["select", "    " + ",\n    ".join(select), f"from {self.fact} f"]
        for j in joins_needed:
            sql.append(f"left join {self.joins[j]['table']} {j} on {self.joins[j]['condition']}")

        where, params = [], []
        for d, vals in filters.items():
            vals = vals if isinstance(vals, (list, tuple)) else [vals]
            if not vals:
                raise MetricError(f"filter {d!r} has no values")
            where.append(f"{self.dimensions[d]['expr']} in ({', '.join('?' for _ in vals)})")
            params += [str(v) for v in vals]
        if date_from:
            where.append(f"{self.date_column} >= cast(? as date)"); params.append(date_from)
        if date_to:
            where.append(f"{self.date_column} <= cast(? as date)"); params.append(date_to)
        if where:
            sql.append("where " + "\n  and ".join(where))
        if dimensions:
            sql.append("group by " + ", ".join(str(i + 1) for i in range(len(dimensions))))
            if order_by_dimensions:
                sql.append("order by " + ", ".join(str(i + 1) for i in range(len(dimensions))))

        meta = {m: {k: self.metrics[m][k] for k in ("description", "owner", "unit", "sensitivity")}
                for m in metrics}
        return CompiledQuery("\n".join(sql), params, list(metrics), dimensions, meta)


def _cli() -> int:
    """Print the SQL the compiler generates - the only place metric SQL is created.

        python -m src.poc.metrics --metrics net_revenue,return_rate --by region,week [--where region=SOUTH]
    """
    import argparse
    import json
    ap = argparse.ArgumentParser(description=_cli.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--metrics", required=True, help="comma-separated metric names")
    ap.add_argument("--by", default="", help="comma-separated dimension names")
    ap.add_argument("--where", action="append", default=[], help="dimension=value[|value...]; repeatable")
    ap.add_argument("--from", dest="date_from"); ap.add_argument("--to", dest="date_to")
    a = ap.parse_args()
    cat = MetricCatalog.load()
    filters = {}
    for w in a.where:
        k, _, v = w.partition("=")
        filters[k.strip()] = [x.strip() for x in v.split("|")]
    try:
        q = cat.compile([m.strip() for m in a.metrics.split(",") if m.strip()],
                        [d.strip() for d in a.by.split(",") if d.strip()], filters, a.date_from, a.date_to)
    except MetricError as e:
        print(f"REFUSED: {e}")
        return 2
    print("-- compiled from metrics/metrics.yml by src/poc/metrics.py")
    print(q.sql + ";")
    print(f"-- parameters: {q.params}")
    print("-- metric metadata: " + json.dumps(q.metadata, indent=2).replace("\n", "\n-- "))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
