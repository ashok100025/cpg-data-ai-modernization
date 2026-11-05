"""The metric compiler is the single source of metric SQL: it must be correct and it must refuse."""
import pytest

from src.poc.metrics import MetricCatalog, MetricError

CAT = MetricCatalog.load()


# ---------- refusal: nothing outside the catalogue gets compiled ----------
@pytest.mark.parametrize("kwargs", [
    dict(metrics=["profit_margin"]),                                   # metric not defined
    dict(metrics=[]),                                                  # nothing asked
    dict(metrics=["net_revenue"], dimensions=["customer"]),            # dimension not defined
    dict(metrics=["net_revenue"], filters={"salary": "x"}),            # filter on unknown dimension
    dict(metrics=["net_revenue"], dimensions=["week", "week"]),        # duplicate
    dict(metrics=["net_revenue"], date_from="last monday"),            # not a date
    dict(metrics=["net_revenue"], filters={"region": []}),             # empty filter
])
def test_refuses_anything_not_in_catalogue(kwargs):
    with pytest.raises(MetricError):
        CAT.compile(**kwargs)


def test_every_metric_has_owner_sensitivity_and_description():
    for name, m in CAT.metrics.items():
        assert m["owner"] and m["description"] and m["sensitivity"] in CAT.spec["sensitivity_levels"], name


def test_filter_values_are_bound_parameters_not_sql():
    q = CAT.compile(["net_revenue"], ["region"], filters={"region": ["SOUTH' or 1=1 --"]})
    assert "or 1=1" not in q.sql and q.params == ["SOUTH' or 1=1 --"]


def test_ratio_metrics_reuse_base_definitions():
    expr = CAT.metric_expr("return_rate")
    assert CAT.metrics["returns_value"]["expr"] in expr and CAT.metrics["gross_sales"]["expr"] in expr


def test_join_added_only_when_needed():
    assert "join" not in CAT.compile(["net_revenue"], ["region"]).sql
    assert "gold.dim_product" in CAT.compile(["net_revenue"], ["category"]).sql


# ---------- correctness against the built warehouse ----------
def test_totals_equal_fact_through_every_dimension(con):
    """No join may duplicate rows: totals by any dimension equal the fact total."""
    fact_rev, fact_units = con.sql("select sum(net_sales_inr), sum(qty) from gold.fct_sales_line").fetchone()
    for dim in CAT.dimensions:
        q = CAT.compile(["net_revenue", "net_units"], [dim])
        rows = con.execute(q.sql, q.params).fetchall()
        assert sum(r[1] for r in rows) == fact_rev, dim
        assert sum(r[2] for r in rows) == fact_units, dim


def test_ratio_equals_hand_calculation(con):
    q = CAT.compile(["return_rate"], ["region"], filters={"region": "SOUTH"})
    (_, rate), = con.execute(q.sql, q.params).fetchall()
    ret, gross = con.sql("select sum(returns_inr), sum(gross_sales_inr) from gold.fct_sales_line "
                         "where region_code_at_sale = 'SOUTH'").fetchone()
    assert rate == pytest.approx(float(ret / gross))


def test_injection_attempt_returns_nothing(con):
    q = CAT.compile(["net_revenue"], ["region"], filters={"region": ["SOUTH' or 1=1 --"]})
    assert con.execute(q.sql, q.params).fetchall() == []


def test_as_was_and_as_is_differ_only_by_reassigned_store(con):
    q_was = CAT.compile(["net_revenue"], ["region"], filters={"region": "WEST"})
    q_is = CAT.compile(["net_revenue"], ["region_as_is"], filters={"region_as_is": "WEST"})
    was = con.execute(q_was.sql, q_was.params).fetchall()[0][1]
    is_ = con.execute(q_is.sql, q_is.params).fetchall()[0][1]
    s003_before_move = con.sql("select sum(net_sales_inr) from gold.fct_sales_line "
                               "where store_code = 'S003' and event_date_local < date '2026-07-01'").fetchone()[0]
    assert is_ - was == s003_before_move


def test_mart_is_built_from_the_compiler(con):
    q = CAT.compile(["net_revenue", "net_units"], ["week", "region", "category", "channel"])
    compiled = con.execute(q.sql, q.params).fetchall()
    mart = con.sql("select week, region, category, channel, net_revenue, net_units from gold.mart_sales_weekly "
                   "order by 1, 2, 3, 4").fetchall()
    assert compiled == mart
