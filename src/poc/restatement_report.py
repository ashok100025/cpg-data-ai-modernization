"""Show what a Finance restatement changed - read-only, from the warehouse.   Run: make demo-restatement

Figures "before" are rebuilt from the daily version table (gold.snp_sales_daily) as they were valid at the
moment of the first approval; "now" are the current versions. Nothing is read from memory or recomputed by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

import duckdb

DB = Path("data/warehouse/cpg.duckdb")


def main() -> int:
    if not DB.exists():
        sys.exit("warehouse not built - run `make all` first")
    c = duckdb.connect(str(DB), read_only=True)
    appr = c.sql("select restatement_id, period, source_system, decision, booking_month, approved_at "
                 "from silver.slv_restatement_approvals order by approved_at").fetchall()
    if not appr:
        print("No restatement approvals yet.")
        return 0
    t0 = min(a[5] for a in appr)
    print("Restatement approvals (Finance):")
    for rid, per, src, dec, book, at in appr:
        n, v = c.execute("select count(*), coalesce(sum(net_sales_inr), 0) from gold.fct_sales_line where restatement_id = ?",
                         [rid]).fetchone()
        print(f"  {rid}  sale month {per}  {src:4}  {dec:15} {('booked in ' + book) if book else '':18} "
              f"-> {n} lines released, net ₹{float(v):,.2f}")

    print("\nStill pending restatement (by sale month):")
    rows = c.sql("select event_month, source_system, sum(pending_lines), sum(pending_inr) from gold.restatement_pending "
                 "group by 1, 2 order by 1, 2").fetchall()
    for m, s, n, v in rows or [("-", "", 0, 0)]:
        print(f"  {m}  {s:4}  {n:>4} lines  ₹{float(v or 0):,.2f}")

    def as_of(month: str, basis: str, at):
        col = "date" if basis == "sale" else "accounting_month"
        cond = f"strftime({col}, '%Y-%m') = ?" if basis == "sale" else "accounting_month = ?"
        if at is None:
            q = f"select coalesce(sum(net_revenue),0) from gold.snp_sales_daily where dbt_valid_to is null and {cond}"
            return float(c.execute(q, [month]).fetchone()[0])
        q = (f"select coalesce(sum(net_revenue),0) from gold.snp_sales_daily where {cond} "
             "and dbt_valid_from <= ? and (dbt_valid_to is null or dbt_valid_to > ?)")
        return float(c.execute(q, [month, at, at]).fetchone()[0])

    print(f"\nNet revenue - as reported before the first approval ({t0:%Y-%m-%d %H:%M}) vs now (from gold.snp_sales_daily):")
    print(f"  {'month':8} {'basis':16} {'before':>16} {'now':>16} {'change':>12}")
    months = sorted({a[1] for a in appr} | {a[4] for a in appr if a[4]})
    for m in months:
        for basis in ("sale", "accounting"):
            b, n = as_of(m, basis, t0), as_of(m, basis, None)
            print(f"  {m:8} {basis + ' month':16} ₹{b:>15,.2f} ₹{n:>15,.2f} {n - b:>+12,.2f}")
    vers = c.sql("select count(*) from (select cell_key from gold.snp_sales_daily group by 1 having count(*) > 1)").fetchone()[0]
    total = c.sql("select count(distinct cell_key) from gold.snp_sales_daily").fetchone()[0]
    print(f"\nVersion table: {total:,} daily cells, {vers:,} with more than one version (old versions kept, valid_to set).")
    q_released = c.sql("select count(*) from silver.slv_sales_quarantine where release_status = 'released'").fetchone()[0]
    q_total = c.sql("select count(*) from silver.slv_sales_quarantine").fetchone()[0]
    print(f"Quarantine: {q_total} rows kept, {q_released} marked released - nothing deleted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
