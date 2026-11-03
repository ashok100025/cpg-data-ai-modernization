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

_Filled in as the PoC is built (Blocks 2–4)._ Target: `make all` locally or `docker build . && docker run …`,
with no cloud account and no API key required.

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
