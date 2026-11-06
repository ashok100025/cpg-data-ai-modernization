# Block 7 – Review guide: read it as the interviewer will

**Status:** review pack prepared 2026-11-06 08:10 IST; Ashok's review completed 15:43 IST – architecture, ADR-004, README in
detail with findings F2–F10; pod plan, readiness, corrections register and Excel reviewed with no further changes. Pushed on approval.

**Purpose:** you review the work critically, decide what to change, cut or defend, and rehearse the
answers you will give on the call. Findings you raise are recorded as **yours** (corrections register:
"Found by: Ashok"); items from section 3 you decide to act on are recorded as *"AI raised it, Ashok decided"*.

---

## 1. Reading order (≈ 60 minutes, highest interview risk first)

| # | Read | Time | Look for |
|---|---|---|---|
| 1 | `docs/architecture/architecture.md` §2 (diagram + component table) | 10 min | Can you explain every box and arrow in 2 minutes? Any component you would not choose? |
| 2 | `architecture.md` §6 (migration phases + exit criteria) | 5 min | Is coexist → reconcile → cut-over realistic for this client? Durations believable? |
| 3 | `docs/adr/ADR-001-lakehouse-platform.md` | 5 min | Would you defend Databricks over Snowflake / Fabric for this client? Is the lock-in statement fair? |
| 4 | `docs/delivery/pod_plan.md` §3 (decision rights) and §4 (conflicts) | 10 min | Do the D/A assignments match how you would run a pod? Is the conflict process yours? |
| 5 | `docs/delivery/readiness.md` – handoff risks | 5 min | Would you rank them the same way? |
| 6 | `docs/corrections_register.md` + `methodology/Methodology.xlsx` (Tool Usage Summary, Coaching Moments) | 10 min | Is every statement accurate? Which coaching moment will you tell in the video? |
| 7 | `README.md` top half | 5 min | First impression in 60 seconds: is the core idea clear? |
| 8 | Section 2 below – answer the questions out loud | 10 min | Where you hesitate, note it as a finding |

## 2. Questions the interviewer is likely to ask – and where the answer is

### Architecture and platform
| Q | Question | Answer lives in |
|---|---|---|
| Q1 | Why Databricks and not Snowflake or Fabric *for this client*? | [ADR-001](../adr/ADR-001-lakehouse-platform.md) options table + consequences |
| Q2 | What is locked in, and what is your exit path? | [ADR-001](../adr/ADR-001-lakehouse-platform.md) "Lock-in"; architecture §1 principle 6 |
| Q3 | Why both Lakeflow pipelines **and** dbt? Isn't that two tools for one job? | architecture §2 component table (see weak point W3) |
| Q4 | How does this scale from the PoC to ~300 M lines/year? | architecture §7 Scale; [ADR-001](../adr/ADR-001-lakehouse-platform.md) validation #2 |
| Q5 | How do you migrate without breaking the existing nightly reports? | architecture §6 – parallel run, reconciliation exit gate |
| Q6 | What does it cost? | architecture §8 – drivers and controls; sizing in the Phase 0 spike (see W7) |

### Data modelling
| Q | Question | Answer lives in |
|---|---|---|
| Q7 | What is the grain of the fact and why that grain? | logical_model.md "Modelling rules" #1 |
| Q8 | A store moved region – how does June revenue report? Who decided? | [ADR-002](../adr/ADR-002-history-and-attribution.md); pod_plan §4 example |
| Q9 | Why not dbt snapshots for SCD2? | [ADR-002](../adr/ADR-002-history-and-attribution.md) option B |
| Q10 | Why is the region stamped on the fact *and* kept in an SCD2 dimension? | logical model – as-was stamp for speed and safety, SCD2 for as-is and attributes (see W14) |
| Q11 | ERP and PIM disagree on pack size – who wins and how do you know? | assumption [A-03](../requirements/assumptions_register.md#a-03); `slv_product_conflicts` |

### Integration and quality
| Q | Question | Answer lives in |
|---|---|---|
| Q12 | A POS gateway re-sends yesterday twice – what happens? | [ADR-004](../adr/ADR-004-late-data-and-corrections.md); quality_rules [DQ-08](../governance/quality_rules.md#dq-08); coaching [C3](../../methodology/coaching_moments.csv) |
| Q13 | A correction arrives 30 days late – what happens and who acts? | [ADR-004](../adr/ADR-004-late-data-and-corrections.md); [DQ-07](../governance/quality_rules.md#dq-07); Finance restatement queue |
| Q14 | A source renames a column without notice? | cicd.md §5; risks [R-03](../governance/risks.md#r-03) |
| Q15 | How do you know an alert works? | monitoring.md principles; decision [D8](../../methodology/decision_log.csv); coaching [C5](../../methodology/coaching_moments.csv) |

### Metrics and forecast
| Q | Question | Answer lives in |
|---|---|---|
| Q16 | How do you guarantee one definition of revenue? | metrics.yml + compiler; `make sql`; block_03 Q4 |
| Q17 | Why is the forecast so simple? Is 14.5% WAPE good? | block_03 – FVA vs baseline; brief says advanced ML not required (see W5) |
| Q18 | What leakage risks exist and how did you test them? | forecast.py docstring; coaching [C8](../../methodology/coaching_moments.csv) |
| Q19 | Why does the forecast use as-is when reporting is as-was? | [ADR-002](../adr/ADR-002-history-and-attribution.md); decision [D10](../../methodology/decision_log.csv) |

### AI
| Q | Question | Answer lives in |
|---|---|---|
| Q20 | Why not let the LLM write SQL – it's more flexible? | [ADR-003](../adr/ADR-003-ai-grounding.md) options |
| Q21 | Someone types "ignore your instructions…" – what happens? | golden set S2; malicious-planner tests; [ADR-003](../adr/ADR-003-ai-grounding.md) |
| Q22 | Does the LLM ever see sales data? | [ADR-003](../adr/ADR-003-ai-grounding.md); access_model §4 – no, only question + catalogue |
| Q23 | You had no API key – so is the AI part real? | [ADR-003](../adr/ADR-003-ai-grounding.md) validation; planner is pluggable; guardrails are the point (see W4) |

### Delivery and leadership
| Q | Question | Answer lives in |
|---|---|---|
| Q24 | Two business units define revenue differently – what do you do? | pod_plan §4 |
| Q25 | How do you split work across three engineers and what do you own yourself? | pod_plan §1–3 |
| Q26 | What is not production-ready and what worries you most at handoff? | readiness.md |
| Q27 | What would you teach engineers about AI-generated code? | ai_assisted_engineering.md |

### Your use of AI
| Q | Question | Answer lives in |
|---|---|---|
| Q28 | How much of this did the AI write, and what did you do? | Tool Usage Summary; corrections register "How to talk about this" |
| Q29 | Give one example where you overrode the AI. | corrections #1, #9 (yours); coaching [C1](../../methodology/coaching_moments.csv), [C6](../../methodology/coaching_moments.csv) |
| Q30 | How do you know the AI's work is correct? | ai_assisted_engineering practices 3–4, 7, 10 |

## 3. Weak points – raised by the AI, for you to decide

Honest list of what an interviewer could challenge. For each: the honest answer today, and a possible
change. **You decide** whether to change anything; if you do, it is recorded as "AI raised it, Ashok decided".

| W | Weak point | Honest answer today | Possible change (your call) |
|---|---|---|---|
| W1 | **Synthetic data only** – 230 k lines vs ~100–300 M/year | The brief allows synthetic data; contracts and patterns are what carry over; scale argued by incremental design, proven only in the [ADR-001](../adr/ADR-001-lakehouse-platform.md) spike | None needed; or add one line in README "scale is designed, not demonstrated" |
| W2 | **PoC on DuckDB, not Databricks** – you are a Databricks practitioner | Chosen so any reviewer can run it without an account ([D2](../../methodology/decision_log.csv)); dbt models are portable | Add a commented `databricks` target in `dbt/profiles.yml` + a short "how to run on Databricks" note – shows portability concretely |
| W3 | **Two transformation tools** (Lakeflow pipelines + dbt) in the target | Lakeflow for streaming ingestion and bronze/silver expectations; dbt for gold, tests, contracts and portability | Keep and state the boundary explicitly; **or** simplify to one tool (e.g. dbt on Databricks + Auto Loader streaming tables) |
| W4 | **Rules planner understands limited phrasing; Claude planner untested** | The safety comes from guardrails, not the planner; golden set grows with real questions | None; or state the pass-rate target for the LLM planner in [ADR-003](../adr/ADR-003-ai-grounding.md) more prominently |
| W5 | **Forecast is simple**; synthetic seasonality is monthly, which flatters seasonal naive | Brief: advanced ML not required – explain suitability, leakage, measurement; FVA measured | Add the "flattered by synthetic data" caveat to the README forecast section |
| W6 | **Monthly batches** make the late-window rule look odd ("14 days after the batch period starts") | Production batches are daily; the rule then reads "14 days after the sale date's batch" | Clarify the rule wording in [ADR-004](../adr/ADR-004-late-data-and-corrections.md) for daily batches |
| W7 | **No cost figures** | Deliberate ([D15](../../methodology/decision_log.csv)): unverifiable prices are easy to challenge; sizing method given | Be ready to explain the sizing method; or add an order-of-magnitude estimate marked "to validate" |
| W8 | **Documents are long** | Every required item is covered | Add a one-page executive summary at the top of the README (problem → design → evidence → what's next) |
| W9 | **Time-box wording** – README says "~1 working day"; the log shows ~8.5 h of work over 3 calendar days | Both are true but the README should match the log exactly | Reword to "≈ 8.5 hours of logged work across three days (see Methodology.xlsx)" |
| W10 | **Pod engineers "to staff"; CODEOWNERS all map to you** | Correct for a PoC; real teams would be named at engagement start | None |
| W11 | **AI wrote most of the text and code** | True and declared; your contribution is constraints, decisions, gates, review, approval | Prepare your own 2-minute account of the design without notes |
| W12 | **dbt Python model for the mart** is unusual | Only way to call the compiler inside dbt; production uses metric views | None |
| W13 | **As-was test hard-codes S003 and the date** | It is a business-rule test for the known move; generic SCD2 tests cover the mechanism | None |
| W14 | **Region stamped on the fact and in the SCD2 dimension** – redundancy | Stamp = fast, safe as-was reporting; dimension = as-is and other attributes | None; be ready to explain |
| W15 | **Finance workload** – 70 corrections held in the demo restatement queue | Depends on real correction rates; measured in Phase 1 | None; or note "per-source windows" as an option in [ADR-004](../adr/ADR-004-late-data-and-corrections.md) |

## 4. How to give your findings

Write them in the chat in any form, for example:

> F1 – architecture §2: I would not use Lakeflow + dbt; use dbt only. Reason: …
> F2 – pod plan: Engineer C has too much; move CI/CD to Engineer A.
> F3 – W9: fix the wording.
> F4 – I can't answer Q6 confidently – explain it to me.

For each finding I will: make the change (or explain), record it in the corrections register (Found by:
Ashok – or "AI raised it, Ashok decided"), add a coaching moment if substantive, and include it in one
commit pushed on your approval.

---

## 5. Findings so far (2026-11-06)

| # | Finding (Ashok) | Decision | Change | Register |
|---|---|---|---|---|
| F1 | What is the "§" symbol? | Clear once explained – keep it | none | – |
| F2 | Add a diagram of the PoC | Yes | `04_poc_architecture` in architecture section 5 + README | #35 |
| F3 | Daily-run step 2 looks like data comes from Lakeflow Jobs | Redraw | Data arrows between layers; Jobs as orchestrator note | #36 |
| F4 | Migration: from where to where? Why reconcile monthly net revenue? | Explain in the doc | From → to table + reconciliation paragraph | #37 |
| F5 | Extension points – did the PDF ask for it? | Yes (NFR) – cite it | Section 9 intro quotes the requirement | #38 |
| F6 | Gantt needs week numbers; durations need stated size assumptions (4 Vs, reports) – 1 TB and few reports could take a month | Yes | Week-numbered Gantt; sizing drivers, S/M/L scenarios, estimating method in architecture section 6; assumption [A-19](../requirements/assumptions_register.md#a-19) | #39 |
| F7 | Open questions: is it showcase? Why UAE? | Option B – keep UAE, state the cause | [A-11](../requirements/assumptions_register.md#a-11) / [A-14](../requirements/assumptions_register.md#a-14) reworded; open questions as a table with owners; [A-19](../requirements/assumptions_register.md#a-19) added | #40 |
| F8 | Add hyperlinks to IDs (A-xx, D-xx, …) | Yes | All IDs in README and docs link to their source; row anchors in assumptions, risks, quality rules | #41 |
| F9 | [ADR-004](../adr/ADR-004-late-data-and-corrections.md): if 1% arrives after 14 days, what do we tell the CEO? What happens in the database after restating? | Build all of it; store a **daily** summary, not monthly | Pending view + AI note; approvals feed, release, accounting month, daily summary + daily version table; walkthrough page; [A-20](../requirements/assumptions_register.md#a-20) | #42, #43 |
| F10 | Is the README Run it section enough for another engineer? | No – add a reviewer quick start | Three run paths, prerequisites, expected output, troubleshooting; `make demo`; Docker runs `make demo` | #47 |

## 6. For submission (Block 9)

- [ ] **Give the reviewers access to the private GitHub repo** (Settings → Collaborators), or make it public – otherwise nobody can clone it.
- [ ] Check the latest CI run is green on the submitted commit.
