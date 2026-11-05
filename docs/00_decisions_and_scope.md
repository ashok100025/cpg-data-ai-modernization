# Decisions locked at start & scope for the time-box

Status: **Locked in Block 1** (2026-11-03). Changes after this point are recorded in
`methodology/decision_log.csv` with the reason.

## Delivery plan (nine blocks)

| # | Block | Output |
|---|---|---|
| 1 | Lock decisions, repo skeleton, start logs | This file, repo layout, methodology logs |
| 2 | Synthetic data → bronze/silver/gold, quality rules, SCD2 | Running pipeline with deliberate data faults |
| 3 | Metric definitions, curated marts, forecast, tests | One metric layer; backtested forecast |
| 4 | Governed AI insight + refusals, Docker, `make`, CI | End-to-end reproducible run |
| 5 | Requirements trace, assumptions, models, contracts, architecture diagram, ADRs | Architecture pack |
| 6 | Governance, risks, pod plan, readiness, CI/CD notes, methodology .xlsx | Delivery pack |
| 7 | Human critical review of AI output → fixes | Coaching moments, corrective commits |
| 8 | Video script, rehearsal, recording | 8–12 min demo |
| 9 | Buffer, final push, submission | Submitted |

## Locked decisions

| ID | Decision | Why | Owner |
|---|---|---|---|
| L1 | Target platform: Azure + Databricks + Delta + Unity Catalog; alternative Snowflake + dbt | Fits a hybrid on-prem→cloud path, one governance plane for data and AI; detailed in ADR-001 | Architect (proposes) / Client platform team (approves) |
| L2 | PoC on Python + DuckDB + dbt, packaged in Docker | Any engineer can run it in minutes with no cloud account; dbt preserves contracts, tests, snapshots and lineage that port to Databricks | Architect |
| L3 | Medallion layering (bronze / silver / gold) | Separates raw replayable history from conformed and consumption layers; maps 1:1 to target | Architect |
| L4 | Metrics defined once in `metrics/metrics.yml`; every consumer reads it | Removes the core client problem (duplicate measure definitions) | Architect + Business metric owners |
| L5 | AI assistant is constrained to metric/dimension selection, never free SQL | Answers stay traceable and policy-checked; detailed in ADR-003 | Architect |
| L6 | LLM provider is pluggable; default is an offline deterministic provider | No API key available for the PoC and reviewers must reproduce outputs; Claude API / Ollama can be switched on by env var | Architect |
| L7 | Commits authored by the candidate; AI co-authorship shown in commit trailers | Brief asks to show how AI tools were used and corrected | Candidate |

## Scope cuts for the time-box (and what closes each)

| Cut | Kept instead | To close in a real engagement |
|---|---|---|
| Optional signals (weather, competitor price, inventory, marketing) not ingested | Promotions only, plus a written value-vs-cost assessment | Value test per signal against forecast error before onboarding |
| Forecast is a baseline, not tuned ML | Seasonal-naive + one simple model, time-based backtest, leakage notes | Feature work with promotions/inventory once data contracts exist |
| No infrastructure-as-code or live cloud deployment | Target design + Docker run path + CI | Terraform + Databricks Asset Bundles in phase 1 |
| Three ADRs, not a full ADR log | Platform, history/attribution, AI grounding | ADR backlog listed in delivery docs |

## Assumptions to confirm with stakeholders (seed – the full register is [`docs/requirements/assumptions_register.md`](requirements/assumptions_register.md), A-01…A-18)

- Net revenue = gross sales − returns − discounts, excluding tax, in reporting currency. **Business owner: Finance.**
- Store moves between regions are reported **as-was** (sale stays with the region at time of sale) by default, with as-is available. **Business owner: Sales Ops.**
- Product master: ERP owns identity, status and pack size; PIM/marketing owns brand and category names. **Business owner: Master Data.**
- Retail calendar is 4-4-5 with weeks starting Monday. **Business owner: Finance.**
- Late-arriving sales are accepted for 14 days; later corrections go through a restatement process. **Business owner: Finance + Data Platform.**
