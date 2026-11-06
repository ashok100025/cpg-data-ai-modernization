"""Governed assistant: golden question set + guardrails that hold even if the planner (LLM) misbehaves."""
import json
import re
from pathlib import Path

import pytest
import yaml

from src.poc.insight.assistant import Assistant
from src.poc.insight.planner import QueryPlan

CASES = yaml.safe_load((Path(__file__).parent / "insight_eval.yml").read_text())["cases"]


@pytest.fixture(scope="module")
def bot(con, tmp_path_factory):
    return Assistant(con=con, audit_path=tmp_path_factory.mktemp("audit") / "audit.jsonl")


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden_question(bot, case):
    r = bot.ask(case["question"], case["role"])
    exp = case["expect"]
    assert r.status == exp["status"], (case["id"], r.answer)
    for key in ("metrics", "dimensions"):
        if key in exp:
            assert r.plan[key] == exp[key], (case["id"], key, r.plan)
    for key in ("date_from", "date_to"):
        if key in exp:
            assert r.plan[key] == exp[key], (case["id"], key, r.plan)
    for dim, vals in exp.get("filters", {}).items():
        assert r.plan["filters"].get(dim) == vals, (case["id"], r.plan["filters"])
    if "only_region" in exp:
        assert r.rows, case["id"]
        assert r.params and set(p for p in r.params if p in {"NORTH", "SOUTH", "WEST", "EAST", "UAE"}) == {exp["only_region"]}
        if "region" in r.columns:
            assert {row[r.columns.index("region")] for row in r.rows} == {exp["only_region"]}


# --------- the planner is untrusted: a misbehaving LLM must not get past the guardrails ---------
class EvilPlanner:
    name = "evil"

    def __init__(self, plan):
        self._plan = plan

    def plan(self, question, context):
        return self._plan


@pytest.mark.parametrize("plan, role, expected", [
    (QueryPlan(metrics=["avg_selling_price"]), "regional_manager_south", "REFUSED_UNAUTHORIZED"),       # too sensitive
    (QueryPlan(metrics=["net_revenue"], filters={"region": ["WEST"]}), "regional_manager_south", "REFUSED_UNAUTHORIZED"),
    (QueryPlan(metrics=["customer_lifetime_value"]), "finance_analyst", "REFUSED_UNSUPPORTED"),         # invented metric
    (QueryPlan(metrics=["net_revenue"], dimensions=["customer_name"]), "finance_analyst", "REFUSED_UNSUPPORTED"),
    (QueryPlan(metrics=["net_revenue"], date_from="2026-01-01'; drop table x; --"), "finance_analyst", "REFUSED_UNSUPPORTED"),
    (QueryPlan(metrics=["net_revenue"], dimensions=["region"]), "regional_manager_south", "ANSWERED_RESTRICTED"),
])
def test_guardrails_hold_whatever_the_planner_returns(con, tmp_path, plan, role, expected):
    plan.date_label = "test"
    bot = Assistant(con=con, planner=EvilPlanner(plan), audit_path=tmp_path / "a.jsonl")
    r = bot.ask("anything", role)
    assert r.status == expected, r.answer
    if expected == "ANSWERED_RESTRICTED":
        assert {row[0] for row in r.rows} == {"SOUTH"}


def test_injected_filter_value_is_a_bound_parameter(con, tmp_path):
    plan = QueryPlan(metrics=["net_revenue"], dimensions=["region"], filters={"region": ["SOUTH' or '1'='1"]},
                     date_label="test")
    r = Assistant(con=con, planner=EvilPlanner(plan), audit_path=tmp_path / "a.jsonl").ask("x", "finance_analyst")
    assert r.status == "ANSWERED" and r.rows == [] and "or '1'='1" not in r.sql


def test_every_number_in_an_answer_comes_from_the_result(bot):
    r = bot.ask("What was net revenue by region last quarter?", "finance_analyst")
    numbers = {n.replace(",", "") for n in re.findall(r"₹([\d,]+)", r.answer)}
    from_rows = {f"{float(row[1]):.0f}" for row in r.rows}
    assert numbers and numbers <= from_rows


def test_relative_dates_resolve_against_data_not_today(bot):
    r = bot.ask("Net revenue last quarter", "finance_analyst")
    assert r.plan["date_to"] <= str(bot.context["as_of"])


def test_every_request_is_audited(con, tmp_path):
    path = tmp_path / "audit.jsonl"
    bot = Assistant(con=con, audit_path=path)
    bot.ask("Net revenue by region", "finance_analyst")
    bot.ask("profit by brand", "finance_analyst")
    bot.ask("Net revenue", "intern")
    recs = [json.loads(line) for line in path.read_text().splitlines()]
    assert [x["status"] for x in recs] == ["ANSWERED", "REFUSED_UNSUPPORTED", "REFUSED_UNAUTHORIZED"]
    assert recs[0]["sql_sha256"] and recs[1]["sql_sha256"] is None


def test_answers_carry_lineage_owner_and_freshness(bot):
    r = bot.ask("Net revenue by category in 2026", "finance_analyst")
    assert r.sql and r.metrics["net_revenue"]["owner"] == "Finance" and "sales up to" in r.data_as_of and r.caveats


def _pending(con, months, regions=None):
    sql = "select coalesce(sum(pending_inr), 0) from gold.restatement_pending where event_month between ? and ?"
    params = list(months)
    if regions:
        sql += f" and region in ({', '.join('?' for _ in regions)})"; params += regions
    return float(con.execute(sql, params).fetchone()[0])


def test_answers_state_pending_restatement_for_the_period(bot, con):
    """ADR-004: an official figure is shown with the late sales still waiting for Finance, if any."""
    r = bot.ask("What was net revenue by region in June 2026?", "finance_analyst")
    expected = _pending(con, ("2026-06", "2026-06"))
    assert r.pending_restatement_inr == pytest.approx(expected)
    assert (expected > 0) == any("pending Finance restatement" in n for n in r.notes)


def test_pending_note_respects_the_role_region_scope(bot, con):
    r = bot.ask("What was net revenue by region in July 2026?", "regional_manager_south")
    assert r.pending_restatement_inr == pytest.approx(_pending(con, ("2026-07", "2026-07"), ["SOUTH"]))
    assert r.pending_restatement_inr <= _pending(con, ("2026-07", "2026-07"))
