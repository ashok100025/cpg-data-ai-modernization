# Block 1 – Repo skeleton, locked decisions, methodology logs

**Status:** built, verified, pushed (commits `728f5db`, `8f4f257`).

Block 1 builds no data or code. It sets up the **container for all three deliverables** and records
the **decisions everything else depends on**.

---

## 1. Repo folder layout

**What:** empty folders for docs, contracts, dbt, metrics, source, tests, methodology.

**Why:** PDF page 3, *"What to Submit → 1. Git Repository"*, lists what the repo must contain. One
home per bullet means nothing is forgotten and the reviewer finds each rubric item where expected.

| PDF bullet (page 3) | Folder |
|---|---|
| Working PoC source, sample data, automated tests, setup instructions | `src/poc/`, `dbt/`, `tests/`, `README.md` |
| Requirements and assumptions register; conceptual & logical models; physical schema and data contracts | `docs/requirements/`, `docs/models/`, `contracts/` |
| Architecture diagram (sources, ingestion, storage… security boundaries) | `docs/architecture/` |
| At least two ADRs | `docs/adr/` |
| Quality rules, access model, lineage, monitoring, risks | `docs/governance/` |
| Pod work split, acceptance criteria, readiness classification, CI/CD notes | `docs/delivery/` |
| Deliverable 3 – methodology spreadsheet | `methodology/` |

## 2. README.md – the front door

| README lines | Point | PDF link |
|---|---|---|
| 9–12 | **Time-box note** – brief allows two weeks, delivered in ~1 day, cuts listed | Page 2: *"State assumptions, trade-offs"* |
| 16–17 | **Every measure is defined once** (`metrics/metrics.yml`) | Page 1: *"Reporting teams maintain separate metric definitions"*, *"without creating separate definitions of the same measures"* – the client's core pain |
| 17–19 | **AI cannot write free SQL** – only picks approved metrics; access-checked; otherwise refused and logged | Problem area 3: *"grounded in approved metrics and access policies"*; functional req: *"unsupported or unauthorized answers are prevented or flagged"* |
| 44–55 | **Stack table** – Target vs Alternative vs PoC substitute | Page 2 "Technology Choice": *"Name the preferred stack and at least one credible alternative"*; *"PoC may use local or lightweight substitutes when they preserve the intended data contracts"* |

Lines 21–37 are the repository map (the folder-to-PDF mapping above).

## 3. docs/00_decisions_and_scope.md – most important file of Block 1

**a) The nine frozen blocks** – how the work is organised.

**b) Locked decisions L1–L7**

| Decision | Plain words | PDF link |
|---|---|---|
| L1 Azure + Databricks; alternative Snowflake | Production platform | Problem area 4: *"state technology choices and alternatives"* |
| L2 PoC on Python + DuckDB + dbt in Docker | Runs on any laptop in minutes, no cloud account | *"Another engineer can run the proof of concept and reproduce its outputs"* |
| L3 Bronze / silver / gold | Raw → cleaned → business-ready | Problem area 2: *"ingestion, validation, transformation, and serving layers"* |
| L4 Metrics defined once in one YAML | One definition of revenue for everyone | Core client pain, page 1 |
| L5 AI picks metrics, never free SQL | Safe, traceable AI | Problem area 3 + *"Not required: a complex autonomous agent"* |
| L6 Pluggable LLM, offline default | No API key; reviewers must reproduce | *"For the AI component, any LLM API or local model works"* |
| L7 Commits by candidate, AI shown as co-author | Honest record of AI use | Page 3: *"The git history is part of the submission. Show how you used AI tools"* |

Each decision names an **owner** (architect / client platform team / business) because page 1 asks:
*"Show which decisions you own, which require business agreement."*

**c) Scope cuts** – what is not done and what would close each gap (uses the PDF's own "What is NOT
required" list plus time-box cuts).

**d) Assumptions to confirm with stakeholders** – revenue definition (Finance), as-was vs as-is region
(Sales Ops), product attribute ownership (Master Data), fiscal calendar (Finance), late-data window
(Finance). PDF page 1: *"Make explicit assumptions… identify which requirements you would confirm with
business and platform stakeholders."* Juniors guess; architects name the decision and its owner.

## 4. requirements.txt – pinned library versions

**Why:** reproducibility – same code, same versions, same results next month.
**Coaching moment C2:** the AI pinned dbt-duckdb 1.9.1 from memory; a clean install showed it was
withdrawn and pulled an incompatible dbt-core. Re-pinned to versions proven by a clean install.
*Lesson: AI knowledge of library versions is stale by design – verify by installing.*

## 5. .gitignore

Keeps generated data, the local database and the Python environment out of git. Data is regenerated
identically from a fixed seed, so committing it adds nothing.

## 6. methodology/ CSV logs – Deliverable 3 started early

`time_log.csv`, `decision_log.csv`, `coaching_moments.csv`, filled **during** the work (honest and
specific), converted to `Methodology.xlsx` in Block 6. Feeds the PDF's Time Log, Decision Log and
Coaching Moments sheets and the video's *"one substantive example where you challenged, corrected,
or rejected generated design or code"*.

- **C1:** AI planned two weeks from the PDF; candidate corrected it from the recruiter's actual ask.
  *Lesson: AI plans from documents; real constraints come from people.*
- **C2:** version pin (above).

## The two commits

- `Block 1: repo skeleton…` – everything above, authored by the candidate with an AI co-author trailer.
- `chore: ignore local handoff dir` – plumbing: local history is packaged into `.handoff/repo.bundle`
  and pushed to GitHub from the cloud side; this stops that package being committed.
