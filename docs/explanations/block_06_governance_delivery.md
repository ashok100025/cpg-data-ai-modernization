# Block 6 – Governance, delivery and the methodology workbook

**Status:** explained 2026-11-05 23:41–00:07 (with Block 5); built and verified locally 00:42–00:50 IST;
pushed on Ashok's approval (00:54).

**In one line:** write down how the platform stays safe (quality, access, lineage, monitoring, risks) and
how a three-engineer pod delivers it and hands it over (pod plan, decision rights, readiness, CI/CD,
AI-engineering practice) – and produce Deliverable 3, the methodology spreadsheet.

---

## Why this block (PDF links)

| PDF requirement | File |
|---|---|
| *"Quality rules, access model, lineage approach, monitoring signals, and risk or failure scenarios"* (page 3) | `docs/governance/` – 5 files |
| *"Pod work split and decision ownership; dependencies, acceptance criteria, and cross-team interfaces"* (page 3) | `docs/delivery/pod_plan.md`, `.github/CODEOWNERS` |
| *"Production-readiness classification per component and prioritized handoff risks"* (page 3) | `docs/delivery/readiness.md` |
| *"CI/CD design notes covering environments, promotion, gates, rollback, and schema or contract change management"* (page 3) | `docs/delivery/cicd.md` |
| Problem area 5 – *"decision rights, interfaces, standards, and acceptance criteria for a three-engineer pod and the teams inheriting the architecture"* | `pod_plan.md` §3–7 |
| Page 1 – *"how you resolve cross-team conflicts, and what you would teach engineers about AI-generated design and code"* | `pod_plan.md` §4, `ai_assisted_engineering.md` |
| Deliverable 3 – Methodology spreadsheet with 5 sheets | `methodology/Methodology.xlsx` (`make methodology`) |
| Video – *"team responsibilities, a cross-team decision, one coaching moment, and a handoff risk"* | pod plan §1/§4, coaching moments, readiness risks |

## What each document says – in plain words

| Document | Key content |
|---|---|
| **quality_rules.md** | 24 rules ([DQ-01](../governance/quality_rules.md#dq-01)…[DQ-24](../governance/quality_rules.md#dq-24)) in three groups – row-level silver rules, table-level dbt tests, semantic/AI tests – each with severity (block / quarantine / collapse / warn), action, owner and the test that enforces it |
| **access_model.md** | 3 classification levels; roles with row scope and max sensitivity; PoC vs Unity Catalog enforcement; example UC row-filter SQL; AI access path; access reviews and break-glass |
| **lineage.md** | 4 levels (row → file, table → table, column → column, answer → SQL); a worked trace of one AI answer back to its CSV file |
| **monitoring.md** | 12 signals with threshold, severity, who is alerted and the runbook action; which exist in the PoC |
| **risks.md** | 14 risk and failure scenarios with likelihood, impact, detection, mitigation, recovery, owner |
| **pod_plan.md** | You as architect/lead + Engineers A/B/C; 7 workstreams (table generated from `pod_plan.csv`); RACI decision rights; the 5-step conflict process with the store-move example; interfaces; standards (definition of done); handoff per component |
| **readiness.md** | 15 components classified PoC-only / prototype / production-candidate, with what is missing; 8 prioritised handoff risks |
| **cicd.md** | 4 environments (one UC catalog each); trunk-based promotion of one versioned bundle; gates per stage (what exists today vs production); rollback for code, data and large changes; additive vs breaking change process; secrets via OIDC and Key Vault |
| **ai_assisted_engineering.md** | The working agreement and 10 practices, each tied to a real incident from this project ([C1](../../methodology/coaching_moments.csv)–[C11](../../methodology/coaching_moments.csv)) |
| **CODEOWNERS** | Makes decision rights enforceable: metric, policy, contract, gold, ADR and workflow changes need their owner's review |

## The workbook (`methodology/Methodology.xlsx`)

| Sheet | Built from | Content |
|---|---|---|
| Time Log | `time_log.csv` + `time_allocation.csv` | Every work block: times, duration, work area, AI tool, generated output, what was verified or changed **and by whom**, estimated minutes per category |
| Tool Usage Summary | computed | Total time; split planning / modelling / build / testing / documentation; time per block; AI contribution (what AI generated vs what the candidate contributed; corrections by who found them; coaching moments; decisions where the AI's suggestion changed); biggest useful output; most material miss |
| Decision Log | `decision_log.csv` | [D1](../../methodology/decision_log.csv)–[D19](../../methodology/decision_log.csv): requirement, options, criteria, chosen design, AI suggestion, evidence, trade-off, owner |
| Pod Plan | `pod_plan.csv` | WS1–WS7: owner, ADR/contract owner, dependencies, acceptance criteria, handoff classification, partner teams |
| Coaching Moments | `coaching_moments.csv` | [C1](../../methodology/coaching_moments.csv)–[C11](../../methodology/coaching_moments.csv): what AI proposed, what changed, why it mattered, what to teach |

Run `make methodology` after any log update; the same command rewrites the pod-plan table in
`pod_plan.md`, so the sheet and the document cannot disagree. Blocks 7–9 add their rows before submission.

---

# Exact inventory – what Block 6 created

| # | File | Purpose |
|---|---|---|
| 1 | `docs/governance/quality_rules.md` | [DQ-01](../governance/quality_rules.md#dq-01)…[DQ-24](../governance/quality_rules.md#dq-24) |
| 2 | `docs/governance/access_model.md` | Classification, roles, enforcement, UC mapping |
| 3 | `docs/governance/lineage.md` | Lineage levels and a worked trace |
| 4 | `docs/governance/monitoring.md` | 12 signals with runbook actions |
| 5 | `docs/governance/risks.md` | [R-01](../governance/risks.md#r-01)…[R-14](../governance/risks.md#r-14) |
| 6 | `docs/delivery/pod_plan.md` | Pod, workstreams, decision rights, conflicts, interfaces, standards, handoff |
| 7 | `docs/delivery/readiness.md` | Readiness per component + handoff risks |
| 8 | `docs/delivery/cicd.md` | Environments, promotion, gates, rollback, change management |
| 9 | `docs/delivery/ai_assisted_engineering.md` | What to teach engineers about AI-generated work |
| 10 | `.github/CODEOWNERS` | Enforceable decision ownership |
| 11 | `methodology/pod_plan.csv`, `methodology/time_allocation.csv` | Sources for the Pod Plan sheet and the category split |
| 12 | `src/poc/build_methodology_xlsx.py`, `make methodology` | Workbook generator |
| 13 | `methodology/Methodology.xlsx` | **Deliverable 3** |
| 14 | README map, glossary, logs ([D18](../../methodology/decision_log.csv)–[D19](../../methodology/decision_log.csv), register #34), this file | Docs |

## Verification

| Check | Result |
|---|---|
| Workbook has exactly the 5 required sheets | ✅ Time Log, Tool Usage Summary, Decision Log, Pod Plan, Coaching Moments |
| Category split reconciles to every time-log row | ✅ the generator refuses to build otherwise |
| Computed counts checked against their sources | ✅ after fixing [D15](../../methodology/decision_log.csv) (register #34) |
| Workbook layout looked at (rendered) | ✅ dark headers, wrapped text, frozen header, filters |
| Pod-plan table in markdown generated from the same CSV | ✅ 7 workstreams |
| Block 5 forward links (`docs/governance/`, `docs/delivery/`) now resolve | ✅ |
| CI for Block 5 commit `cd1cb37` | ✅ test and docker jobs green |

## How you can verify it yourself
1. Open `methodology/Methodology.xlsx` in Excel – check each of the 5 sheets, especially **Tool Usage Summary**.
2. Read `docs/delivery/pod_plan.md` §3 (decision rights) and §4 (conflict process) – likely interview topics.
3. Read `docs/delivery/ai_assisted_engineering.md` – the "what I would teach" answer for the video.
4. `make methodology` – rebuilds the workbook from the CSVs.

## Assumptions agreed for this block
| # | Assumption |
|---|---|
| 1 | Pod = Ashok (architect/lead) + Engineers A (data platform), B (modelling, metrics, forecast), C (AI, serving, DevOps) |
| 2 | Seven workstreams – migration and reconciliation is the seventh, led by the architect |
| 3 | Category split of each time block is an estimate, marked as such |
