"""Gold mart: weekly sales by region (as-was), category (as-was) and channel.

Built as a dbt Python model so it stays in dbt's build order, tests and lineage, while every
formula comes from metrics/metrics.yml through the metric compiler - no measure is re-written here.

Ratios (return_rate, avg_selling_price, promo_revenue_share) are correct at THIS grain only; never
sum or average them across rows - ask the compiler for the grain you need instead.
"""
import sys
from pathlib import Path


def model(dbt, session):
    dbt.config(materialized="table")
    # declare dependencies so dbt builds this after the curated model (lineage + ordering)
    dbt.ref("fct_sales_line"); dbt.ref("dim_date"); dbt.ref("dim_product"); dbt.ref("dim_store")

    sys.path.insert(0, str(Path.cwd()))          # dbt runs from the repo root (see Makefile)
    from src.poc.metrics import MetricCatalog

    catalog = MetricCatalog.load()
    q = catalog.compile(
        metrics=["gross_sales", "returns_value", "net_revenue", "units_sold", "units_returned", "net_units",
                 "promo_revenue", "return_rate", "avg_selling_price", "promo_revenue_share"],
        dimensions=["week", "region", "category", "channel"],
    )
    return session.sql(q.sql)
