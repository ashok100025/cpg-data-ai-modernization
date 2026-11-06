"""Gold daily summary: one row per sale date x accounting month x region (as-was) x category (as-was) x channel,
additive measures only. Weekly, monthly, fiscal-period or any other figure is derived from it on the fly; ratios
are recomputed from the additive measures, never stored. Built through the metric compiler (one definition).
It is also what the version table gold.snp_sales_daily snapshots on every run."""
import sys
from pathlib import Path


def model(dbt, session):
    dbt.config(materialized="table")
    dbt.ref("fct_sales_line"); dbt.ref("dim_date"); dbt.ref("dim_product"); dbt.ref("dim_store")
    sys.path.insert(0, str(Path.cwd()))
    from src.poc.metrics import MetricCatalog

    dims = ["date", "accounting_month", "region", "category", "channel"]
    q = MetricCatalog.load().compile(
        metrics=["gross_sales", "returns_value", "net_revenue", "units_sold", "units_returned", "net_units",
                 "promo_revenue", "restated_lines"],
        dimensions=dims)
    return session.sql(f"""
        select md5(concat_ws('|', {', '.join(dims)})) as cell_key, *
        from ({q.sql}) t""")
