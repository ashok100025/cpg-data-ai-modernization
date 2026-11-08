# Block 5 – Architecture pack: requirements, models, architecture, ADRs

**Status:** explained 2026-11-05 23:41–00:07 (with Block 6); built and verified locally 00:07–00:20 IST;
files verified present by Ashok 00:40; pushed on approval. `architecture.md` reviewed in detail by Ashok in Block 7
(findings F2–F7: PoC diagram, daily-run diagram, migration scope and sizing, open questions, extension points).

**In one line:** write down *what* is being built and *why* – the requirements trace, the assumptions
to confirm, the data models, the target architecture with its migration path, and the four key decisions.

---

## Why this block (PDF links)

| PDF requirement (page 3, Git repository) | File |
|---|---|
| *"Requirements and assumptions register"* | `docs/requirements/requirements_trace.md`, `assumptions_register.md` |
| *"Conceptual and logical data models; representative physical schema and data contracts"* | `docs/models/conceptual_model.md`, `logical_model.md`, `physical_schema.md` (+ `contracts/` from Block 2) |
| *"Architecture diagram showing sources, ingestion, storage, transformation, serving, AI integration, security boundaries, and operational flows"* | `docs/architecture/architecture.md` + 3 diagrams |
| *"At least two ADRs explaining options, decisions, consequences, and validation needed before production"* | `docs/adr/ADR-001…004` |
| FR1 *"A requirements trace links business questions to source data, canonical entities, measures, transformations, and consumers"* | `requirements_trace.md` §1 |
| Problem area 4 – *"target cloud architecture and a phased path… security, cost, operations, and DevOps… choices and alternatives"* | `architecture.md` §2–8, [ADR-001](../adr/ADR-001-lakehouse-platform.md) |
| NFR1 – *"scale, availability, security, access control, privacy, observability, lineage, data quality, cost, and recovery"* | `architecture.md` §7–8 |
| NFR4 – *"ownership, contracts, and extension points for the receiving teams"* | `architecture.md` §9 (+ pod plan in Block 6) |
| Page 1 – *"identify which requirements you would confirm with business and platform stakeholders"* | `assumptions_register.md` (stakeholder table) |

## What each document says – in plain words

| Document | Read it to learn | Key content |
|---|---|---|
| **Requirements trace** | Why each table and metric exists | 8 business questions traced to sources → entities → measures → transformations → consumers; every brief requirement mapped to where it is met and the test that proves it; how the "NOT required" list was respected |
| **Assumptions register** | What could be wrong and who must say so | 18 assumptions ([A-01](../requirements/assumptions_register.md#a-01)…[A-19](../requirements/assumptions_register.md#a-19)), each with the stakeholder who confirms it, the impact if wrong, how to validate; a table of questions per stakeholder (Finance, Sales Ops, Master Data, Planning, Governance, Platform/Security). The IDs match the code comments |
| **Conceptual model** | The business vocabulary | 9 entities (sales line, product, store, region, channel, calendar, promotion, currency rate, source system), their relationships (ER diagram), source of truth, and what changes over time |
| **Logical model** | How it becomes tables, independent of a database | Fact + 4 dimensions (ER diagram with keys), grain, business and surrogate keys, history type per entity, which measures are additive, 5 modelling rules, layer responsibilities |
| **Physical schema** | Every real table and column | **Generated from dbt** (`make schema-doc`): 22 tables/views with types, descriptions and tests, plus 6 sources; section 1 = the Databricks design (catalog per environment, Delta, liquid clustering, MERGE, time travel, tags, metric views, naming, retention) |
| **Architecture** | The target platform and how to get there | Principles; target diagram; component table with alternatives and PoC substitutes; security boundaries; daily-run sequence and failure handling; PoC → target mapping; 4-phase migration with exit gates; NFR table; cost drivers and controls; extension points; open questions |
| **[ADR-001](../adr/ADR-001-lakehouse-platform.md)** | Why Databricks | Databricks + UC vs Snowflake + dbt vs Fabric on 8 criteria; lock-in is moderate (Delta and dbt are portable, UC and Lakeflow are not); 4 validations (network spike, load test, cost sizing, security review) |
| **[ADR-002](../adr/ADR-002-history-and-attribution.md)** | How history works | Type 1 vs dbt snapshots vs SCD2-from-extracts vs stamp-on-fact; SCD2 from extracts chosen because any environment can be rebuilt with history; as-was reporting, as-is forecasting |
| **[ADR-003](../adr/ADR-003-ai-grounding.md)** | Why the AI is safe | Text-to-SQL vs vendor semantic layer vs catalogue plan + guardrails; LLM never writes SQL or sees data; validations: LLM vs golden set, red-team, pilot |
| **[ADR-004](../adr/ADR-004-late-data-and-corrections.md)** | How late and corrected data are handled | Apply all vs reject vs window + restatement; retries collapsed first (the bug found in Block 2), 14-day window, Finance owns the process |

## The three diagrams

| Diagram | Shows | Files |
|---|---|---|
| Target architecture | 6 numbered zones: sources → ingestion → lakehouse (UC) → build/orchestrate → serving & AI → consumers; the private Azure boundary; the AI path ("question + catalogue, never data"; "compiled SQL + forced row filters") | `docs/architecture/diagrams/01_target_architecture.{mmd,png}` |
| Daily run | Numbered sequence from 02:00 file arrival to 06:00 readiness; the failure branch (stop downstream, alert, gold keeps last good version); recovery note | `02_daily_run.{mmd,png}` |
| Migration phases | Gantt P0–P3 with the reconciliation exit gate and warehouse retirement | `03_migration_phases.{mmd,png}` |

Each diagram exists as **Mermaid text** (renders on GitHub, editable in git) and as a **PNG** (for the
video and local viewing). The two ER diagrams are in the model docs, also with PNGs.

---

# Exact inventory – what Block 5 created

| # | File | Purpose |
|---|---|---|
| 1 | `docs/requirements/requirements_trace.md` | BQ1–BQ8 trace; P1–P5, FR1–FR5, NFR1–NFR4 → where met → proof; "NOT required" stance |
| 2 | `docs/requirements/assumptions_register.md` | [A-01](../requirements/assumptions_register.md#a-01)…[A-19](../requirements/assumptions_register.md#a-19) + questions per stakeholder |
| 3 | `docs/models/conceptual_model.md` + `diagrams/conceptual_model.png` | Entities, relationships, business rules |
| 4 | `docs/models/logical_model.md` + `diagrams/logical_model.png` | Keys, grain, history, measures, modelling rules |
| 5 | `docs/models/physical_schema.md` | **Generated** – target design + 22 tables, 6 sources |
| 6 | `src/poc/build_schema_doc.py`, `make schema-doc` | Generator |
| 7 | `docs/architecture/architecture.md` | Target architecture (10 sections) |
| 8 | `docs/architecture/diagrams/01–03 .mmd + .png` | Diagram sources and renders |
| 9 | `docs/adr/README.md`, `ADR-001…004` | Decision records |
| 10 | `dbt/models/gold/_gold.yml` (update) | Descriptions for all 28 fact columns (seen missing in the generated schema) |
| 11 | README (map + architecture image), `docs/00_decisions_and_scope.md` (pointer), glossary, logs, corrections register | Docs |

## Verification

| Check | Result |
|---|---|
| All 5 Mermaid diagrams render (mermaid-cli) | ✅ 0 errors |
| Rendered PNGs looked at for readability | ✅ after re-layout (see changes) |
| Physical schema regenerated from dbt after the description changes | ✅ 22 tables/views, 6 sources; fact columns all described |
| dbt parse + build after the YAML edits | ✅ 61 tests pass (1 expected warning – October demo data) |
| Assumption IDs in code ([A-01](../requirements/assumptions_register.md#a-01)…[A-10](../requirements/assumptions_register.md#a-10)) match the register's meanings | ✅ checked one by one |
| ADR "Related" decision IDs exist in the decision log | ✅ [D1](../../methodology/decision_log.csv)–[D14](../../methodology/decision_log.csv) |
| Forward references to Block 6 (`docs/governance/`, `docs/delivery/`) | ⏳ files created in Block 6 – links resolve after that push |

## Changes made during the build (AI output corrected)

| What | Why |
|---|---|
| Target architecture re-laid out top-to-bottom | First render put the sources at the bottom with 8 crossing lines – unreadable in a video (#31) |
| Daily-run diagram: removed `;` from labels | Mermaid treats `;` as a statement end – parse error (#32) |
| Gantt section labels shortened | First bar overlapped the "Phase 0" label (#32) |
| Fact column descriptions added | The generated physical schema showed most fact columns blank (#33) |
| Broken `decimal(12, …` YAML repaired | A regex edit split quoted types at the comma; `dbt parse` caught it (#30) |

## How you can verify it yourself

1. Open the PNGs in Finder: `docs/architecture/diagrams/` and `docs/models/diagrams/`.
2. In VS Code, preview (Cmd + Shift + V): `docs/architecture/architecture.md`, then the four ADRs.
3. `make schema-doc` – regenerates `docs/models/physical_schema.md`; compare with `make preview TABLE=gold.fct_sales_line`.
4. Pick any assumption ID in the register (e.g. [A-05](../requirements/assumptions_register.md#a-05)) and search the repo for it – it leads to the code that uses it.
5. After the push, open the same files on GitHub – the Mermaid blocks render as diagrams there.

## Assumptions agreed for this block

| # | Assumption |
|---|---|
| 1 | Diagrams in Mermaid + PNG exports |
| 2 | Physical schema generated from dbt |
| 3 | Cost as drivers, sizing approach and FinOps controls – no price figures |
| 4 | RPO/RTO as proposed targets to confirm ([A-13](../requirements/assumptions_register.md#a-13)) |
| 5 | Azure Central India; data residency for a second country open – UAE in the PoC data ([A-14](../requirements/assumptions_register.md#a-14)) |
| 6 | Ingestion: ADF / Lakeflow Connect with self-hosted IR + Auto Loader |
| 7 | Indicative phase durations, to confirm ([A-18](../requirements/assumptions_register.md#a-18)) |
| 8 | Four ADRs |
| 9 | Eight business questions in the trace |
