# Architecture Decision Records

Each ADR records one consequential decision: context, options, decision, consequences and the
validation needed before production. Decisions are also summarised in `methodology/decision_log.csv`
(Decision Log sheet).

| ADR | Title | Type | Status | Owner |
|---|---|---|---|---|
| [ADR-001](ADR-001-lakehouse-platform.md) | Lakehouse platform: Azure Databricks + Unity Catalog | Technology choice | Proposed | Architect → client platform board |
| [ADR-002](ADR-002-history-and-attribution.md) | History: SCD2 dimensions, as-was reporting, as-is forecasting | Data modelling trade-off | Proposed | Architect → Sales Ops, Master Data |
| [ADR-003](ADR-003-ai-grounding.md) | AI insight through the metric catalogue, not free text-to-SQL | AI / governance | Proposed | Architect → Data Governance |
| [ADR-004](ADR-004-late-data-and-corrections.md) | Late data and corrections: 14-day window + restatement queue | Integration trade-off | Proposed | Architect → Finance |

*Proposed* = implemented in the PoC; becomes *Accepted* once the validation listed in each ADR is done.
