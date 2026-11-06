# Pod plan, decision rights and interfaces

How a three-engineer pod led by the architect delivers this architecture, who decides what, how
cross-team conflicts are resolved, and how the receiving teams take it over.

## 1. The pod

| Role | Person | Focus | Owns decisions on |
|---|---|---|---|
| **Architect and pod lead** | Ashok | Architecture, ADRs, standards, stakeholder alignment, reconciliation, coaching | Technology and design choices (with platform board approval), standards, definition of done, priorities within the pod |
| **Engineer A – Data platform** | (to staff) | Ingestion, source contracts, silver quality and history, platform pipelines | Ingestion patterns, quality-rule implementation, source onboarding sequence |
| **Engineer B – Modelling, metrics, forecast** | (to staff) | Gold model, metric catalogue implementation, forecast, reconciliation support | Model structure within [ADR-002](../adr/ADR-002-history-and-attribution.md), forecast model selection by backtest |
| **Engineer C – AI, serving, DevOps** | (to staff) | Assistant, access policy implementation, CI/CD, observability | Assistant implementation within [ADR-003](../adr/ADR-003-ai-grounding.md), pipeline and deployment tooling |

Every workstream has a **named second** (pairing) so no knowledge sits with one person (risk [R-12](../governance/risks.md#r-12)).

## 2. Workstreams

*Generated from `methodology/pod_plan.csv` by `make methodology` – the same file feeds the Pod Plan sheet.*

<!-- POD_PLAN_TABLE:START -->
| ID | Workstream | Owner | ADR / contract owner | Dependencies | Acceptance criteria | Handoff | Partner teams |
|---|---|---|---|---|---|---|---|
| WS1 | Ingestion and source contracts | Engineer A (Data platform) | ADR-004 / source contracts signed by each source owner | P0 landing zone and networking; access to POS / e-com / ERP / PIM / store feeds | All feeds land on schedule into UC volumes; every source has a signed contract (schema, key, cadence, owner); replay of any batch reproduces bronze; quarantine rate < 0.5% in steady state | Production-candidate -> Data Platform team | Retail IT (POS), Digital Commerce, Master Data, Sales Ops |
| WS2 | Silver quality, de-duplication and history | Engineer A (with Engineer B) | ADR-002 / ADR-004; quality-rule owners in quality_rules.md | WS1 | DQ-01..DQ-20 implemented as tests; incremental run equals full rebuild (content hash); SCD2 tests green; anomaly alert proven to fire on a known-bad batch | Production-candidate -> Data Platform team | Finance (late window), Sales Ops, Master Data |
| WS3 | Curated model and metric catalogue | Engineer B (Modelling and metrics) | ADR-002 / metrics.yml - each metric's business owner (Finance for revenue) | WS2; metric owners nominated | fct_sales_line contract enforced; metric views generated from metrics.yml; net revenue reconciles with the on-prem warehouse within agreed tolerance for 2 closed months; every metric has an owner and sign-off | Production-candidate -> Analytics engineering | Finance, Commercial analytics, BI team |
| WS4 | Revenue and demand forecast | Engineer B | Decision D11 / Demand Planning lead | WS3 | Backtest shows positive forecast value added vs seasonal naive per measure; confidence label on every series; accuracy drift monitor live; planners accept the grain and horizon | Prototype -> Data Science / Planning | Demand Planning, Supply Chain |
| WS5 | Governed AI assistant and access policy | Engineer C (AI and serving) | ADR-003 / access policy owned by Data Governance | WS3; identity mapping (A-15); LLM endpoint approved | Golden set 100% on refusal and restriction cases and >= 90% on answer cases; red-team session passed; LLM never receives rows (verified); pilot BU feedback positive; audit log retained | Prototype -> AI platform team | Data Governance, Security, pilot business unit |
| WS6 | Platform, CI/CD and observability | Engineer C (with Engineer A) | ADR-001 / D14 / platform team for runners and workspaces | P0 foundation | dev / test / prod deployed from CI only (Asset Bundles + Terraform); rollback drill done; monitoring signals routed with runbooks; cost tags and budgets live | Production-candidate -> Platform team | Cloud platform team, Security, FinOps |
| WS7 | Migration and reconciliation (parallel run) | Ashok (Architect and pod lead) with Engineer B | P1 exit gate / Finance signs the reconciliation | WS3; on-prem warehouse access | Reconciliation report per metric and month signed by Finance; every difference explained by a documented rule; report cut-over plan and decommission list agreed | Lead-owned -> programme / BI team | Finance, BI team, on-prem warehouse team |
<!-- POD_PLAN_TABLE:END -->

Sequence: WS6 and WS1 start in P0/P1 → WS2 → WS3 → (WS4, WS5, WS7 in parallel). WS7 gates the move of
reporting (P1 exit), WS5 is piloted with one business unit in P3.

## 3. Decision rights

**D** = decides · **C** = consulted · **I** = informed · **A** = approves (when someone else decides)

| Decision | Architect (Ashok) | Engineers | Business owner | Platform / Security | Data Governance |
|---|---|---|---|---|---|
| Platform and technology choices ([ADR-001](../adr/ADR-001-lakehouse-platform.md)) | D | C | I | **A** | C |
| Data model, history, attribution ([ADR-002](../adr/ADR-002-history-and-attribution.md)) | D | C | **A** – Sales Ops, Master Data | I | I |
| **Metric definitions** (`metrics.yml`) | C | C (implement) | **D** – metric owner (Finance for revenue) | – | A (sensitivity) |
| Access policy and sensitivity | C | C (implement) | C | C | **D** |
| Late-data window and restatement ([ADR-004](../adr/ADR-004-late-data-and-corrections.md)) | C (mechanism) | I | **D** – Finance | I | I |
| Source contract changes | C | D (Eng A, technical) | **A** – source owner | I | I |
| Breaking change to a gold contract | **D** | C | C – exposure owners | I | I |
| Forecast model selection | C | **D** – Eng B, by backtest | A – Demand Planning | – | – |
| AI scope, golden set, refusal rules ([ADR-003](../adr/ADR-003-ai-grounding.md)) | C | D – Eng C proposes | C | C | **A** |
| Production deployment | A (release) | D – Eng C runs | I | A (change process) | – |
| Budget and cost limits | C | I | **D** – sponsor | C | – |

## 4. Resolving cross-team conflicts

The most likely conflict is **two business units defining the same measure differently** (risk [R-06](../governance/risks.md#r-06)), or
**Finance and Sales Ops disagreeing on attribution** (the store-move case). The process:

1. **Make the difference visible** – compute both versions side by side on real data (the metric compiler
   makes this a one-line change); quantify the gap per month and region.
2. **Metric owners' forum** (weekly, chaired by the Finance metric owner; architect facilitates) decides
   within one week, using the data.
3. **Outcome is one of two:** one certified definition, or **two named metrics** (e.g. `net_revenue` and
   `net_revenue_incl_tax`) – never two meanings behind one name.
4. **Escalate** to the programme sponsor only if the forum cannot decide; the architect presents options
   and consequences, not a recommendation for one side.
5. **Record** the outcome as an ADR or decision-log entry and update `metrics.yml` through a reviewed pull request.

*Example from this case study:* Sales Ops wanted store S003's history to move to WEST; Finance needed
closed SOUTH numbers to stay fixed. Resolution: **as-was is the reporting default** (Finance), **as-is is
available as `region_as_is`** for planning (Sales Ops) – [ADR-002](../adr/ADR-002-history-and-attribution.md).

## 5. Interfaces with other teams

| Interface | With | What is agreed | Where |
|---|---|---|---|
| Inbound data | Source system owners | Schema, business key, cadence, delivery semantics, late-data rule, change notice | `contracts/source_contracts.yml` |
| Curated data | All consumers | Grain, columns and types, semantics, freshness, versioning | `contracts/fct_sales_line.yml` (enforced) |
| Metrics | BI team, Planning, AI | Names, definitions, owners, sensitivity | `metrics/metrics.yml` → metric views |
| Access | Data Governance, Security | Roles, row scope, sensitivity, audit | `policies/access_policy.yml` → UC |
| Platform | Cloud platform team | Workspaces, networking, runners, budgets | Terraform, Asset Bundles (CI/CD notes) |
| Consumers registry | Every consuming team | Owner, purpose, dependencies | dbt exposures |

## 6. Standards (definition of done)

- **Models:** key tests (`unique`, `not_null`) on every model; description on every model and gold column; gold changes respect the contract.
- **Metrics:** every metric has description, owner, unit, sensitivity; changes approved by the owner (CODEOWNERS).
- **Code review:** two reviewers for gold, metrics, access policy and CI; one for the rest.
- **Tests must be able to fail:** a new rule or guardrail ships with a case that breaks it (mutation check) – see the AI-assisted engineering guide.
- **AI-generated code** is reviewed like any other code, labelled in the commit, and never merged without tests.
- **Docs:** an explanation per change of significance; ADR for consequential decisions; lineage and schema docs generated.
- **CI green** on every pull request; no direct pushes to `main`.

## 7. Handoff to receiving teams

| Component | Receiving team | Handoff includes |
|---|---|---|
| Ingestion, silver, gold, contracts | Data Platform team | Runbooks (monitoring.md), contracts, tests, CODEOWNERS update |
| Metric catalogue and metric views | Analytics engineering / BI | Owner list, change process, `make sql` usage |
| Forecast | Data Science / Planning | Backtest report, confidence labels, retraining guide |
| AI assistant | AI platform team + Data Governance | Golden set, guardrail tests, audit retention, red-team results |
| CI/CD and environments | Platform team | Bundles, Terraform, rollback runbook |

Readiness per component and the prioritised handoff risks: [readiness.md](readiness.md).
