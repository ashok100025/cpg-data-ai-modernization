"""Governed question answering: plan -> guardrails -> execute -> answer -> audit.

The planner (rules or LLM) only proposes a plan. Everything after it is deterministic:
  1. the plan is validated against the metric catalogue (unknown metric/dimension -> REFUSED_UNSUPPORTED)
  2. the access policy is applied (sensitivity -> REFUSED_UNAUTHORIZED; region scope forced as a filter)
  3. SQL comes only from the metric compiler (bound parameters, read-only connection)
  4. the answer text is a template filled ONLY from the result rows - no model writes numbers
  5. every request, allowed or refused, is written to the audit log
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

from src.poc.insight.planner import QueryPlan, get_planner
from src.poc.insight.policy import AccessPolicy
from src.poc.metrics import MetricCatalog, MetricError

DB = Path("data/warehouse/cpg.duckdb")
AUDIT = Path("outputs/audit/insight_audit.jsonl")
CAVEATS = [
    "Regions are as-was (region of the store on the sale date) unless 'current region' is asked.",
    "Amounts are INR, tax excluded, converted at monthly average FX.",
    "Demand (net units) is observed demand - lost sales from stock-outs are not visible.",
]

ANSWERED, RESTRICTED = "ANSWERED", "ANSWERED_RESTRICTED"
UNSUPPORTED, UNAUTHORIZED = "REFUSED_UNSUPPORTED", "REFUSED_UNAUTHORIZED"


@dataclass
class Response:
    status: str
    answer: str
    question: str
    role: str
    plan: dict
    columns: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    sql: str | None = None
    params: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    data_as_of: str | None = None
    pending_restatement_inr: float = 0.0
    notes: list = field(default_factory=list)
    caveats: list = field(default_factory=list)
    audit_id: str = ""

    def to_dict(self) -> dict:
        return self.__dict__


class Assistant:
    def __init__(self, con: duckdb.DuckDBPyConnection | None = None, planner=None,
                 audit_path: Path | None = AUDIT):
        self.con = con or duckdb.connect(str(DB), read_only=True)
        self.catalog = MetricCatalog.load()
        self.policy = AccessPolicy.load()
        self.planner = planner or get_planner()
        self.audit_path = audit_path
        self.context = self._context()

    # ------------------------------------------------------------ grounding context for the planner
    def _context(self) -> dict:
        c = self.con
        as_of = c.sql("select max(event_date_local) from gold.fct_sales_line").fetchone()[0]
        last_ingest = c.sql("select max(ingested_at) from gold.fct_sales_line").fetchone()[0]
        q = c.execute("""select fiscal_year, fiscal_quarter, min(date_day), max(date_day) from gold.dim_date
                         group by 1, 2 having max(date_day) <= ? order by 3 desc limit 1""", [as_of]).fetchone()
        fy_start = c.execute("select min(date_day) from gold.dim_date where fiscal_year = "
                             "(select fiscal_year from gold.dim_date where date_day = ?)", [as_of]).fetchone()[0]
        fys = {int(r[0][2:6]): {"label": r[0], "from": r[1].isoformat(), "to": r[2].isoformat()}
               for r in c.sql("select fiscal_year, min(date_day), max(date_day) from gold.dim_date group by 1").fetchall()}
        vocab = {
            "region": [r[0] for r in c.sql("select distinct region_code from gold.dim_store order by 1").fetchall()],
            "category": [r[0] for r in c.sql("select distinct category_name from gold.dim_product order by 1").fetchall()],
            "brand": [r[0] for r in c.sql("select distinct brand_name from gold.dim_product order by 1").fetchall()],
            "channel": [r[0] for r in c.sql("select distinct channel from gold.fct_sales_line order by 1").fetchall()],
        }
        return {
            "as_of": as_of, "last_ingested_at": str(last_ingest),
            "last_complete_fiscal_quarter": {"label": f"{q[0]} Q{q[1]} ({q[2]} to {q[3]})",
                                             "from": q[2].isoformat(), "to": q[3].isoformat()},
            "fiscal_year_start": fy_start.isoformat(), "fiscal_years": fys, "vocabulary": vocab,
            "metric_descriptions": {k: v["description"] for k, v in self.catalog.metrics.items()},
            "dimension_descriptions": {k: v["description"] for k, v in self.catalog.dimensions.items()},
        }

    # ------------------------------------------------------------ main entry
    def ask(self, question: str, role: str) -> Response:
        plan: QueryPlan = self.planner.plan(question, self.context)
        resp = self._govern(question, role, plan)
        resp.data_as_of = f"sales up to {self.context['as_of']} (last load {self.context['last_ingested_at']})"
        self._audit(resp)
        return resp

    def _govern(self, question: str, role: str, plan: QueryPlan) -> Response:
        base = dict(question=question, role=role, plan=plan.to_dict())
        if role not in self.policy.roles:
            return Response(UNAUTHORIZED, f"Refused: unknown role {role!r}. Access is denied by default.", **base)
        if plan.unsupported_reason:
            return Response(UNSUPPORTED, f"I can't answer that: {plan.unsupported_reason}. "
                            f"Approved metrics: {', '.join(sorted(self.catalog.metrics))}.", **base)
        try:   # the plan is untrusted: re-validate it with the compiler before anything else
            self.catalog.compile(plan.metrics, plan.dimensions, plan.filters, plan.date_from, plan.date_to)
        except MetricError as e:
            return Response(UNSUPPORTED, f"I can't answer that: {e}", **base)

        sens = {m: self.catalog.metrics[m]["sensitivity"] for m in plan.metrics}
        decision = self.policy.check(role, sens, plan.filters)
        if not decision.allowed:
            return Response(UNAUTHORIZED, f"Refused: {decision.reason}.", **base)

        filters = dict(plan.filters)
        notes = []
        if decision.forced_filters:
            filters.update(decision.forced_filters)
            notes.append(decision.reason[0].upper() + decision.reason[1:] + ".")
        q = self.catalog.compile(plan.metrics, plan.dimensions, filters, plan.date_from, plan.date_to)
        cur = self.con.execute(q.sql, q.params)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        if len(rows) > self.policy.max_rows:
            notes.append(f"Result has {len(rows)} rows; showing the first {self.policy.max_rows}. "
                         "Narrow the question for a complete answer.")
            rows = rows[: self.policy.max_rows]
        status = RESTRICTED if decision.restricted else ANSWERED
        pending = self._pending_restatement(plan, filters)
        if pending > 0:
            total = None
            if "net_revenue" in plan.metrics:
                j = cols.index("net_revenue")
                total = sum(float(r[j] or 0) for r in rows)
            share = f" ({100 * pending / total:.1f}% of the figure shown)" if total else ""
            notes.append(f"₹{pending:,.0f}{share} of late sales for this period is pending Finance restatement and is "
                         "not included above (ADR-004).")
        return Response(status, self._compose(plan, cols, rows), sql=q.sql, params=q.params, metrics=q.metadata,
                        columns=cols, rows=[list(r) for r in rows], notes=notes, caveats=CAVEATS,
                        pending_restatement_inr=pending, **base)

    # ------------------------------------------------------------ completeness: late sales awaiting Finance
    def _pending_restatement(self, plan: QueryPlan, filters: dict) -> float:
        """Pending restatement value for the months the answer covers, within the same region scope
        (the role's forced region filter or the question's region filter). Defined in metrics.yml
        completeness_signals.pending_restatement."""
        sig = self.catalog.spec.get("completeness_signals", {}).get("pending_restatement")
        if not sig:
            return 0.0
        where, params = [], []
        if plan.date_from:
            where.append(f"{sig['month_column']} >= ?"); params.append(plan.date_from[:7])
        if plan.date_to:
            where.append(f"{sig['month_column']} <= ?"); params.append(plan.date_to[:7])
        if filters.get("region"):
            where.append(f"{sig['region_column']} in ({', '.join('?' for _ in filters['region'])})")
            params += list(filters["region"])
        if "category" in filters:
            where.append(f"category in ({', '.join('?' for _ in filters['category'])})"); params += list(filters["category"])
        sql = f"select coalesce(sum({sig['value']}), 0) from {sig['table']}" + (" where " + " and ".join(where) if where else "")
        try:
            return float(self.con.execute(sql, params).fetchone()[0])
        except duckdb.CatalogException:
            return 0.0

    # ------------------------------------------------------------ answer text: template over result rows only
    def _fmt(self, metric: str, v) -> str:
        if v is None:
            return "n/a"
        unit = self.catalog.metrics[metric]["unit"]
        if unit == "ratio":
            return f"{float(v) * 100:.2f}%"
        if unit.startswith("INR"):
            return f"₹{float(v):,.2f}" if "per" in unit else f"₹{float(v):,.0f}"
        return f"{int(v):,}"

    def _compose(self, plan: QueryPlan, cols: list, rows: list) -> str:
        names = " and ".join(m.replace("_", " ") for m in plan.metrics)
        scope = f" by {', '.join(plan.dimensions)}" if plan.dimensions else ""
        filt = "; ".join(f"{k} = {', '.join(v)}" for k, v in plan.filters.items())
        head = f"{names[0].upper() + names[1:]}{scope}, {plan.date_label}" + (f" ({filt})" if filt else "") + ":"
        if not rows:
            return head + " no matching sales."
        nd = len(plan.dimensions)
        lines = []
        for r in rows[:25]:
            label = " / ".join(str(x) for x in r[:nd]) or "Total"
            vals = ", ".join(f"{m.replace('_', ' ')} {self._fmt(m, r[nd + i])}" for i, m in enumerate(plan.metrics))
            lines.append(f"  - {label}: {vals}")
        more = f"\n  … {len(rows) - 25} more rows in the result table" if len(rows) > 25 else ""
        return head + "\n" + "\n".join(lines) + more

    # ------------------------------------------------------------ audit
    def _audit(self, r: Response) -> None:
        r.audit_id = uuid.uuid4().hex[:12]
        if not self.audit_path:
            return
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        rec = {"audit_id": r.audit_id, "ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "role": r.role, "question": r.question, "status": r.status, "planner": r.plan.get("planner"),
               "plan": r.plan, "sql_sha256": hashlib.sha256((r.sql or "").encode()).hexdigest() if r.sql else None,
               "params": r.params, "rows_returned": len(r.rows), "notes": r.notes}
        with self.audit_path.open("a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
