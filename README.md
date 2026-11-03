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

## Run it

Requires Python 3.10+. No cloud account or API key.

```bash
make setup             # virtualenv + pinned dependencies
make all               # land synthetic data, build bronze -> silver -> gold, run 52 data tests
make demo-incremental  # land October: late rows, corrections, bad rows -> incremental run
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

### Explore the results

Everything is built locally in one DuckDB file, **`data/warehouse/cpg.duckdb`** (schemas `ref`, `bronze`,
`silver`, `gold`). DuckDB is serverless and is installed by `make setup` – nothing else is needed.

```bash
make inspect                          # every schema/table with row counts, reconciliation, quarantine by reason
make preview TABLE=gold.dim_store     # first 20 rows of any table or view (ROWS=50 for more)
make query SQL="select region_code_at_sale, sum(net_sales_inr) as net_inr from gold.fct_sales_line group by 1"
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
