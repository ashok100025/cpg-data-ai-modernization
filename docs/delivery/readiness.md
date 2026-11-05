# Production-readiness classification

**PoC-only** = demonstrates the idea; replaced in production. **Prototype** = the design and logic carry
over, but it needs hardening, scale or real-world validation. **Production-candidate** = the logic and
tests carry over largely as-is once ported to the target platform.

| Component | Classification | What carries over | What is missing for production | Workstream |
|---|---|---|---|---|
| Synthetic data generator | **PoC-only** | Fault scenarios become test fixtures | Real feeds and connectors | WS1 |
| DuckDB warehouse, Makefile orchestration | **PoC-only** | – | Databricks + Unity Catalog, Lakeflow Jobs | WS6 |
| Source contracts (`contracts/source_contracts.yml`) | **Production-candidate** | Structure and rules | Signatures from real source owners; real schedules | WS1 |
| Bronze (text-first, sources, file lineage) | **Production-candidate** (pattern) | Text-first, lineage columns, append-only | Auto Loader streaming tables, rescued data | WS1 |
| Silver conformance, quality rules, quarantine | **Production-candidate** | Rules DQ-01…DQ-09, retry/correction handling | `MERGE` instead of delete+insert; real thresholds | WS2 |
| SCD2 dimensions from extracts | **Production-candidate** | Logic and tests | Effective-from dates if sources provide them (A-08) | WS2 |
| Gold fact + contract | **Production-candidate** | Model, contract, tests | dbt-databricks port, liquid clustering, incremental gold | WS3 |
| Metric catalogue + compiler | **Production-candidate** (definitions) / **Prototype** (compiler) | `metrics.yml` definitions and owners | Generate UC metric views; compiler kept for the assistant only | WS3 |
| Weekly mart | **Prototype** | Grain and reconciliation test | Consumers to read metric views directly | WS3 |
| Forecast | **Prototype** | Backtest method, confidence labels, leakage tests | Real history, promotions as a driver, moving holidays, MLflow, drift monitoring | WS4 |
| AI assistant | **Prototype** | Architecture (plan → guardrails → compiler → audit), golden set, policy | LLM planner tested, real identity, red-team, pilot, audit table, UI | WS5 |
| Access policy | **Prototype** | Roles and rules | UC groups, row filters, tags, metric-view grants (A-15) | WS5 |
| Monitoring | **Prototype** | DQ summary and anomaly rule | Freshness, volume, drift, cost signals routed to on-call (monitoring.md) | WS6 |
| CI (GitHub Actions) + Docker | **Production-candidate** (pattern) | Gates and test suite | Environments, Asset Bundles, Terraform, approvals | WS6 |
| Documentation (ADRs, models, explanations) | **Production-candidate** | All | Kept current through CODEOWNERS and generated docs | All |

## Prioritised handoff risks

| # | Risk | Why it ranks here | Mitigation before handoff |
|---|---|---|---|
| 1 | **Assumptions A-01…A-18 unconfirmed** – especially the revenue definition (A-01) and late window (A-05) | Every number depends on them | Confirm in P0 discovery; P1 reconciliation proves them |
| 2 | **Reconciliation with the on-prem warehouse not yet done** | Business will not trust a new number that differs unexplained | WS7 parallel run with Finance sign-off before cut-over |
| 3 | **AI assistant not validated with a real LLM or real users** | Planner quality and user trust unknown | Golden set on the real endpoint, red-team, one-BU pilot (ADR-003) |
| 4 | **Identity and access mapping not built** (A-15) | Policy is only as good as group membership | Map Entra ID groups → UC in P0; access review process |
| 5 | **Forecast trained on synthetic data** | Real seasonality, promotions and stock-outs differ | Re-run backtest on real history; keep confidence labels |
| 6 | **Scale untested** (230 k vs ~100–300 M lines/year) | Incremental design is right but unmeasured | Load test in the ADR-001 spike |
| 7 | **UAE data residency open** (A-14) | Could force a design change | Legal review in P0 |
| 8 | **Knowledge concentration in a small pod** | R-12 | Seconds per workstream, explanations folder, CODEOWNERS |
