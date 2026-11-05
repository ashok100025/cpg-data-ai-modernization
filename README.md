# CPG Data & AI Modernization — Solution Architecture & PoC

Case study submission for a Principal Data / Solution Architect role.
A mid-size CPG company has fragmented sales, product, store and promotion data across
on-prem and cloud systems, and reporting teams maintain **separate definitions of the same
measures**. This repository contains the target architecture, the decisions behind it, a
runnable proof of concept, and the delivery plan for a three-engineer pod.

> **Time-box.** The brief allows two weeks; the hiring team asked for the earliest possible
> submission. This was delivered in ~1 working day as nine fixed blocks. Every required item is
> covered; depth was deliberately traded for breadth, and every cut is listed in
> [`docs/00_decisions_and_scope.md`](docs/00_decisions_and_scope.md) with what would be needed to close it.

## The one idea this design is built around

**Every measure is defined once** (in `metrics/metrics.yml`) and that single definition is used by
the curated model, the BI/SQL layer, the forecast and the AI assistant. The AI assistant cannot
write free SQL — it can only select approved metrics and dimensions, which are then checked against
the caller's access policy before a templated query runs. Anything else is refused and logged.

## Repository map

| Path | What it holds |
|---|---|
| `docs/00_decisions_and_scope.md` | Locked decisions, assumptions, scope cuts for the time-box |
| `docs/requirements/` | Requirements trace & assumptions register |
| `docs/models/` | Conceptual, logical and physical data models |
| `contracts/` | Data contracts per source and per curated product |
| `docs/architecture/` | Target architecture diagram, security boundaries, operational flows |
| `docs/adr/` | Architecture Decision Records |
| `docs/governance/` | Quality rules, access model, lineage, monitoring, risk & failure scenarios |
| `docs/delivery/` | Pod plan, decision rights, interfaces, readiness classification, CI/CD design |
| `dbt/` | PoC transformation project (bronze → silver → gold) |
| `metrics/` | Single source of metric definitions (semantic layer for the PoC) |
| `src/poc/` | Synthetic data generator, forecast, governed AI insight |
| `tests/` | Automated tests run in CI |
| `methodology/` | Time log, decision log, coaching moments → methodology spreadsheet |
| `docs/corrections_register.md` | Every problem found in AI output, how it was found, who spotted it, the fix |
| `docs/explanations/` | Block-by-block walkthroughs and glossary |

## Run it

Requires Python 3.10+. No cloud account or API key.

```bash
make setup             # virtualenv + pinned dependencies
make all               # land data, build bronze -> silver -> gold -> marts, forecast, run all tests
make demo-incremental  # land October: late rows, corrections, bad rows -> incremental run + re-forecast
make test              # 26 Python tests: metric compiler, forecast, leakage guards
```

What the pipeline proves (verified on every run):

| Fault injected at source | How it is handled | Where to see it |
|---|---|---|
| Retries (exact re-sends, incl. next batch) | Recognised by content hash, collapsed | `silver.slv_dq_batch_summary.exact_retries_collapsed` |
| Corrections (same key, new values) | Latest ingested version wins (delete+insert) | `silver.slv_sales` |
| Corrections / late lines beyond 14 days | Held for Finance restatement, not applied | `silver.slv_sales_quarantine` (`LATE_BEYOND_WINDOW`) |
| Unknown SKU, negative price, missing store | Quarantined with reason | `silver.slv_sales_quarantine` |
| Schema drift (new column, `'3.0'` as quantity) | Text-first bronze + typed silver | `brz_ecom_orders`, `slv_sales_conformed` |
| Store moved region / product reclassified | SCD2; facts join as-was | `gold.dim_store`, `gold.dim_product`, test `assert_store_reassignment_is_as_was` |
| ERP vs PIM attribute conflict | ERP wins; conflict published | `silver.slv_product_conflicts` |

Incremental and full rebuild produce identical facts (same rows, units, revenue and content hash).

### Metrics and forecast (Block 3)

**One definition per measure.** `metrics/metrics.yml` defines every measure once (net revenue, net units
= demand, return rate, average selling price, promotion share …) with owner, unit and sensitivity.
`src/poc/metrics.py` is the only code that turns metric names into SQL; the weekly mart, the forecast
and the AI assistant all go through it. Unknown metrics, dimensions or filters are refused; filter
values are bound parameters.

**Forecast.** `make forecast` (part of `make all`): weekly net revenue and net units per category ×
region, 8 weeks ahead, using **as-is** region/category (future sales happen in today's structure;
reporting stays as-was). Two explainable models, chosen by a rolling-origin backtest:

| Measure | Model | Backtest WAPE | Bias | Value added vs baseline |
|---|---|---|---|---|
| net_revenue | seasonal naive × recent trend (**selected**) | 14.5% | +3.4% | +22.5% |
| net_revenue | seasonal naive (baseline) | 18.8% | −15.4% | – |
| net_units | seasonal naive × recent trend (**selected**) | 12.6% | +2.3% | +30.3% |
| net_units | seasonal naive (baseline) | 18.1% | −15.9% | – |

Every forecast row carries a **confidence** label from its own series' backtest error (19 high, 4 medium,
2 low – the single-product *Healthy Snacks* category). Leakage is tested: a deliberately leaked
backtest fails `make test`. Tables: `gold.mart_sales_weekly`, `gold.forecast_weekly`,
`gold.forecast_accuracy`, `gold.forecast_series_accuracy`, `gold.forecast_backtest`.

Limitations: demand is *observed* demand (no inventory, so stock-outs are invisible); moving holidays
(e.g. Diwali) are not modelled; production would forecast as-of ingestion time, not event time.

### Explore the results

Everything is built locally in one DuckDB file, **`data/warehouse/cpg.duckdb`** (schemas `ref`, `bronze`,
`silver`, `gold`). DuckDB is serverless and is installed by `make setup` – nothing else is needed.

```bash
make inspect                          # every schema/table with row counts, reconciliation, quarantine by reason
make preview TABLE=gold.dim_store     # first 20 rows of any table or view (ROWS=50 for more)
make query SQL="select region_code_at_sale, sum(net_sales_inr) as net_inr from gold.fct_sales_line group by 1"
make sql METRICS=net_revenue,return_rate BY=region,week   # the SQL the metric compiler generates
```

All three are read-only and need no extra install.

Optional – browse it in a SQL workbench (needs the DuckDB CLI, e.g. `brew install duckdb`), from the repo root:

```bash
duckdb -ui data/warehouse/cpg.duckdb
```

Run from the repo root: bronze views read the landed CSVs via a relative path.

Using **DBeaver** instead: New Database Connection → DuckDB → path `data/warehouse/cpg.duckdb`, tick
*Read-only connection* (so `make` can rebuild while it is open), and add the bootstrap query
`SET file_search_path = '<absolute path to this repo>';` so bronze views resolve their CSV paths. If you
get a storage-version error, update the DuckDB driver in Driver Manager (the file is built with DuckDB 1.5.6).

## Technology summary

| Layer | Target (production) | Credible alternative | PoC substitute (same contracts) |
|---|---|---|---|
| Cloud | Azure | AWS | Local / Docker |
| Lakehouse & compute | Azure Databricks, Delta Lake | Snowflake | DuckDB |
| Transformation | Lakeflow Declarative Pipelines + dbt | dbt on Snowflake | dbt-duckdb |
| Governance & lineage | Unity Catalog | Snowflake Horizon / Purview | dbt docs lineage + policy file |
| Semantic layer | Databricks metric views | dbt Semantic Layer | `metrics/metrics.yml` + compiler |
| Orchestration | Lakeflow Jobs | Airflow / ADF | Makefile |
| AI | Azure OpenAI or Claude via Databricks Model Serving | Bedrock | Pluggable: offline rules (default) / Claude API / Ollama |
| CI/CD | GitHub Actions + Databricks Asset Bundles | Azure DevOps | GitHub Actions |
