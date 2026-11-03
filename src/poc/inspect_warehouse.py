"""Look at what the pipeline built. Read-only; run from the repo root.

    make inspect                                   # every schema/table with row counts, reconciliation, quarantine
    make preview TABLE=gold.dim_store [ROWS=20]    # first rows of one table or view
    make query SQL="select ... from gold.fct_sales_line ..."   # any read-only SQL
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import duckdb

DB = Path("data/warehouse/cpg.duckdb")
SCHEMAS = ("ref", "bronze", "silver", "gold")


def connect():
    if not DB.exists():
        sys.exit(f"{DB} not found - run `make all` first.")
    con = duckdb.connect(str(DB), read_only=True)
    con.sql(f"SET file_search_path = '{Path.cwd()}'")   # lets bronze views resolve their relative CSV paths
    return con


def show(con, sql: str, rows: int) -> None:
    rel = con.sql(sql)
    rel.show(max_rows=rows, max_width=200)


def summary(con) -> int:
    print(f"Database: {DB.resolve()}  ({DB.stat().st_size / 1e6:.0f} MB)\n")

    objs = con.sql(f"""select table_schema, table_name, table_type from information_schema.tables
                       where table_schema in {SCHEMAS} order by
                       list_position(['ref','bronze','silver','gold'], table_schema), table_name""").fetchall()
    print(f"{'schema':8}{'object':30}{'type':7}{'rows':>10}")
    print("-" * 55)
    for schema, name, kind in objs:
        rows = con.sql(f'select count(*) from "{schema}"."{name}"').fetchone()[0]
        print(f"{schema:8}{name:30}{'view' if kind == 'VIEW' else 'table':7}{rows:>10,}")

    landed, held = con.sql("select sum(rows_landed), sum(rows_quarantined) from silver.slv_dq_batch_summary").fetchone()
    fact = con.sql("select count(*) from gold.fct_sales_line").fetchone()[0]
    dupes = landed - held - fact
    print(f"\nReconciliation: {landed:,} landed - {held:,} quarantined - {dupes:,} duplicate versions "
          f"(retries + corrections) = {fact:,} fact lines")

    print("\nQuarantine by reason:")
    for reason, src, n in con.sql("""select dq_reason, source_system, count(*) from silver.slv_sales_quarantine
                                     group by all order by 3 desc""").fetchall():
        print(f"  {reason:22}{src:6}{n:>6,}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", metavar="SCHEMA.TABLE")
    ap.add_argument("--sql")
    ap.add_argument("--rows", type=int, default=20)
    a = ap.parse_args()
    con = connect()
    if a.preview:
        if not re.fullmatch(r"(ref|bronze|silver|gold)\.[a-z_0-9]+", a.preview):
            sys.exit("TABLE must look like <ref|bronze|silver|gold>.<name>, e.g. gold.dim_store")
        n = con.sql(f"select count(*) from {a.preview}").fetchone()[0]
        print(f"{a.preview}: {n:,} rows - showing up to {a.rows}")
        show(con, f"select * from {a.preview} limit {a.rows}", a.rows)
        return 0
    if a.sql:
        show(con, a.sql, a.rows)
        return 0
    return summary(con)


if __name__ == "__main__":
    sys.exit(main())
