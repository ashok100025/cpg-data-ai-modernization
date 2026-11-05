# ADR-001 – Lakehouse platform: Azure Databricks + Unity Catalog

- **Status:** Proposed (PoC built on the same patterns) · **Date:** 2026-11-03
- **Decision owner:** Architect proposes; client platform/architecture board approves
- **Related:** D1, D2, D14 · assumptions A-14, A-15

## Context
Sales, product, store and promotion data sit in an on-prem warehouse with nightly ETL plus cloud
object storage. The client needs one governed foundation for analytics, forecasting and AI that scales
across business units, controls commercially sensitive data, and avoids separate metric definitions.
Existing skills include Spark/SQL; Azure is the assumed cloud.

## Options

| Criterion | **A. Azure Databricks + Unity Catalog** | B. Snowflake + dbt | C. Microsoft Fabric |
|---|---|---|---|
| One governance plane for data **and** AI (grants, row filters, lineage, model serving) | Strong – UC covers tables, volumes, metric views, models | Good for data (Horizon); AI services separate | Good integration with Power BI; governance maturing |
| Batch + streaming ingestion of files and on-prem sources | Auto Loader, Lakeflow Connect, streaming tables | Snowpipe; streaming via Snowpipe Streaming | Data Factory, eventstreams |
| Python forecasting / ML next to the data | Native (jobs, MLflow) | Snowpark | Notebooks / Spark |
| Open storage format, portability | **Delta** (open), readable by other engines | Proprietary storage (Iceberg tables possible) | Delta in OneLake |
| Semantic layer | UC metric views | dbt Semantic Layer / semantic views | Power BI semantic models |
| Operational effort | Higher – compute policies, networking | Lowest – mostly managed | Low–medium; capacity-based |
| Cost model | DBU consumption; needs FinOps discipline | Credit consumption; simple | Capacity units; risk of over/under-sizing |
| Team skills (Spark, SQL, Python; prior Databricks delivery) | Best fit | SQL-strong teams | Power BI-centric teams |

## Decision
**Option A – Azure Databricks with Unity Catalog**, Delta Lake on ADLS Gen2, Lakeflow for ingestion
and pipelines, dbt for gold models and tests, UC metric views for certified metrics.

## Consequences
- **+** One place for grants, row filters, sensitivity tags, lineage and audit across data, metrics and the AI endpoint.
- **+** Open Delta format and dbt + YAML metrics keep the transformation and semantic logic **portable** (the PoC runs the same models on DuckDB).
- **−** More platform engineering (networking, compute policies, cost controls) than Snowflake.
- **−** DBU-based cost needs active FinOps (architecture §8).
- **Lock-in:** moderate – storage is open; UC governance and Lakeflow pipelines are platform-specific. The exit path is Delta + dbt models + YAML metrics.

## Validation needed before production
1. Spike in the client tenant: VNet injection, private endpoints, self-hosted IR to the on-prem warehouse.
2. Load test with one business unit's real volumes: incremental bronze → gold within the 06:00 target.
3. Cost sizing from that spike against the budget; compare with a Snowflake estimate on the same workload.
4. Security review of UC row filters and metric-view grants against the access model.
