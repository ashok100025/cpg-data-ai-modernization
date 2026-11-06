"""ADR-004 restatement mechanism: nothing deleted, lines (not totals) change, closed months protected, versions kept.
Runs on whatever state the warehouse is in; the approval-specific checks skip until Finance has approved something
(CI runs them after `make demo-restatement`)."""
import pytest


def approvals(con):
    return con.sql("select restatement_id, period, decision, booking_month from silver.slv_restatement_approvals").fetchall()


def test_quarantine_keeps_every_late_line(con):
    """Releasing never deletes: every late line ever received is still in quarantine."""
    late = con.sql("select count(*) from silver.slv_sales_conformed where dq_reason = 'LATE_BEYOND_WINDOW'").fetchone()[0]
    kept = con.sql("select count(*) from silver.slv_sales_quarantine where dq_reason = 'LATE_BEYOND_WINDOW'").fetchone()[0]
    assert late == kept


def test_pending_view_equals_unreleased_late_lines(con):
    q = con.sql("select coalesce(sum(value_inr), 0) from silver.slv_sales_quarantine "
                "where release_status = 'pending_restatement'").fetchone()[0]
    p = con.sql("select coalesce(sum(pending_inr), 0) from gold.restatement_pending").fetchone()[0]
    assert q == p


def test_daily_summary_rolls_up_to_any_period(con):
    """The daily summary is enough to derive weekly / monthly figures - same as the fact."""
    d = con.sql("select strftime(date, '%Y-%m') m, sum(net_revenue) from gold.agg_sales_daily group by 1 order by 1").fetchall()
    f = con.sql("select strftime(event_date_local, '%Y-%m') m, sum(net_sales_inr) from gold.fct_sales_line group by 1 order by 1").fetchall()
    assert d == f


def test_restated_lines_and_closed_months(con):
    appr = approvals(con)
    if not appr:
        pytest.skip("no restatement approved yet - run make demo-restatement")
    for rid, period, decision, booking in appr:
        rows = con.execute("select strftime(event_date_local, '%Y-%m'), accounting_month from gold.fct_sales_line "
                           "where restatement_id = ?", [rid]).fetchall()
        assert rows, f"{rid} released nothing"
        assert all(sale == period for sale, _ in rows)
        expected_acct = period if decision == "RESTATE" else booking
        assert all(acct == expected_acct for _, acct in rows), rid


def test_book_in_current_leaves_closed_month_unchanged(con):
    """BOOK_IN_CURRENT: the closed sale month keeps its previously reported accounting-month figure."""
    appr = [a for a in approvals(con) if a[2] == "BOOK_IN_CURRENT"]
    if not appr:
        pytest.skip("no BOOK_IN_CURRENT approval yet")
    for rid, period, _, booking in appr:
        assert con.execute("select count(*) from gold.fct_sales_line where restatement_id = ? and accounting_month = ?",
                           [rid, period]).fetchone()[0] == 0


def test_version_table_keeps_old_versions(con):
    if not approvals(con):
        pytest.skip("no restatement approved yet")
    changed = con.sql("select count(*) from (select cell_key from gold.snp_sales_daily group by 1 having count(*) > 1)").fetchone()[0]
    closed = con.sql("select count(*) from gold.snp_sales_daily where dbt_valid_to is not null").fetchone()[0]
    assert changed > 0 and closed >= changed
