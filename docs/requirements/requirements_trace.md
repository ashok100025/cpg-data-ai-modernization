# Requirements trace

Links every business question to the source data, canonical entities, measures, transformations and
consumers that answer it (functional requirement 1 of the brief), then maps every requirement in the
brief to where it is met and the test or evidence that proves it.

## 1. Business questions → sources → entities → measures → transformations → consumers

| ID | Business question | Source data | Canonical entities | Measures (`metrics/metrics.yml`) | Transformations | Consumers |
|---|---|---|---|---|---|---|
| BQ1 | What is net revenue by region, category, channel and period – one number everyone agrees on? | POS, e-commerce, store master, ERP + PIM product, FX | Sales line, Store, Region, Product, Channel, Calendar, FX rate | `net_revenue`, `gross_sales`, `returns_value` | bronze → `slv_sales_conformed` → `slv_sales` → `fct_sales_line` (+ `dim_*`) → metric compiler → `mart_sales_weekly` | Sales reporting (exposure), AI assistant, Finance |
| BQ2 | What demand and revenue should we expect in the next 8 weeks, and how much can we trust it? | as BQ1 | Sales line, Product (as-is), Store (as-is), Calendar | `net_units`, `net_revenue` | … → compiler → `src/poc/forecast.py` → `forecast_weekly`, `forecast_accuracy`, `forecast_series_accuracy` | Demand planning (exposure `revenue_forecast`) |
| BQ3 | Where are returns high? | POS (RETURN lines), e-commerce (refunds) | Sales line (signed qty) | `return_rate`, `returns_value`, `units_returned` | sign conformance in silver → fact → compiler | Category managers, AI assistant |
| BQ4 | How dependent are we on promotions? | as BQ1 + promotions calendar | Sales line, Promotion | `promo_revenue`, `promo_revenue_share` (commercially sensitive) | promotion match in `fct_sales_line` → compiler | Trade marketing, Finance (restricted) |
| BQ5 | What price do we actually realise per unit? | as BQ1 | Sales line, Product | `avg_selling_price` (commercially sensitive) | compiler (ratio of `net_revenue` / `net_units`) | Commercial (restricted) |
| BQ6 | Can we trust today's numbers – what arrived, what was held and why? | all sales feeds | Sales line (all versions) | rows landed / valid / quarantined / late | `slv_dq_batch_summary`, `slv_sales_quarantine`, anomaly test | Data Platform on-call, Finance (restatements) |
| BQ7 | Can a manager ask a question in plain English and get a safe, traceable answer? | the curated model | all of the above | any certified metric the role may see | planner → guardrails → compiler → template answer → audit | Business users (exposure `ai_insight_assistant`) |
| BQ8 | How did a region perform like-for-like after a store moved? | store master history | Store (SCD2), Region | `net_revenue` by `region` vs `region_as_is` | `dim_store` SCD2 → as-was / as-is dimensions | Sales Ops, Planning |

## 2. Brief requirement → where it is met → proof

### Problem areas

| # | Brief asks | Where | Proof |
|---|---|---|---|
| P1 | Entities, measures, grain, keys, history, data contracts; conceptual, logical, physical models | `docs/models/`, `contracts/`, `metrics/metrics.yml` | dbt contract on `fct_sales_line`; SCD2 tests |
| P2 | Ingestion, validation, transformation, serving; batch + incremental, schema drift, late data, dedup, lineage, recovery | `dbt/models/`, [ADR-004](../adr/ADR-004-late-data-and-corrections.md), `docs/governance/lineage.md` | `make demo-incremental`; incremental = full refresh (content hash); quarantine reasons |
| P3 | Governed analytics, revenue forecasting, LLM grounded in approved metrics and access policies | `metrics/`, `src/poc/forecast.py`, `src/poc/insight/`, [ADR-003](../adr/ADR-003-ai-grounding.md) | 65 Python tests incl. golden set and leakage test |
| P4 | Target cloud architecture, phased path, security, cost, operations, DevOps, choices and alternatives | `docs/architecture/architecture.md`, [ADR-001](../adr/ADR-001-lakehouse-platform.md) | – (design) |
| P5 | Decision rights, interfaces, standards, acceptance criteria for a 3-engineer pod and inheriting teams | `docs/delivery/` (Block 6) | – (design) |

### Functional requirements

| # | Brief asks | Where | Proof |
|---|---|---|---|
| FR1 | Requirements trace from business questions to consumers | this document, section 1 | – |
| FR2 | Sample data flow: ingest, quality rules, history, queryable curated model | `src/poc/generate_data.py`, `dbt/` | `make all` → 73 dbt tests; `make inspect` reconciliation |
| FR3 | Analytics or forecast from actual data with grain, assumptions, validation | `mart_sales_weekly`, `forecast.py`, `block_03` explanation | backtest WAPE 14.5% vs 18.8% baseline; `test_stored_backtest_used_only_data_before_each_origin` |
| FR4 | AI insight uses approved, traceable results; unsupported / unauthorized prevented or flagged | `src/poc/insight/`, `policies/access_policy.yml` | `tests/insight_eval.yml` (19 cases), malicious-planner tests, audit log |
| FR5 | Another engineer can run the PoC and reproduce outputs | `Makefile`, `Dockerfile`, README | CI `test` and `docker` jobs green; deterministic seed |

### Non-functional requirements

| # | Brief asks | Where | Proof |
|---|---|---|---|
| NFR1 | Scale, availability, security, access control, privacy, observability, lineage, DQ, cost, recovery | `architecture.md` §7–8, `docs/governance/` | monitoring test fires on the October incident |
| NFR2 | Deployment / container run path; automated validation or CI | `Dockerfile`, `.github/workflows/ci.yml` | CI run on commit `828859d`: both jobs green |
| NFR3 | ≥ 2 ADRs incl. one technology choice and one modelling or integration trade-off | `docs/adr/ADR-001…004` | – |
| NFR4 | Ownership, contracts, extension points for receiving teams | `contracts/`, `architecture.md` §9, `docs/delivery/pod_plan.md` | dbt contract fails build on breaking change |

### What the brief says is NOT required – how it is respected

| Not required | Our stance |
|---|---|
| Production-scale platform | PoC on DuckDB with the same contracts; target designed, not built (`readiness.md`, Block 6) |
| Advanced ML | Seasonal naive × trend; suitability, leakage and measurement documented instead |
| Complex autonomous agent | Constrained planner + deterministic guardrails |
| Single vendor choice as an end in itself | [ADR-001](../adr/ADR-001-lakehouse-platform.md) compares three platforms; portability via Delta, dbt and the YAML metric layer |
