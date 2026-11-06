# Corrections register

Every problem found in AI-generated plans, code or documents during this case study, how it was
found, who spotted it, and what was changed. Kept alongside the methodology spreadsheet (Coaching
Moments, Decision Log) and the git history, and consistent with both.

**Spotted by** – *Ashok*: found or demanded by the candidate. *AI self-check*: found by the AI while
verifying its own work, inside the review process Ashok set (explain → agree → build → verify → push).
*AI, from Ashok's question*: Ashok's question exposed the gap; the AI found the cause and proposed the fix.

## Index

| Spotted by | Items |
|---|---|
| **Ashok** | #1, #2, #9, #10, #35–#43, #47 |
| **AI, from Ashok's question** | #13, #14, #15, #22, #23, #28, #29 |
| AI self-check | #3–#8, #11, #12, #16–#21, #24–#27, #30–#34, #44–#46 |

## Corrections

### #1 · Block 0 · AI planned 2 weeks, the window in the brief
- **Found by:** **Ashok** – recruiter had asked for the earliest submission
- **Fix:** Re-planned to ~1 day in 9 fixed blocks with documented scope cuts
- **Why it mattered:** Real constraints come from stakeholders, not documents · *[C1](../methodology/coaching_moments.csv), [D4](../methodology/decision_log.csv)*

### #2 · Block 0 · AI assumed an LLM API key was available
- **Found by:** **Ashok** – Ashok has only a chat subscription
- **Fix:** Pluggable LLM provider with an offline deterministic default
- **Why it mattered:** Reviewers must reproduce the AI part without keys · *[D3](../methodology/decision_log.csv)*

### #3 · Block 1 · Version pin `dbt-duckdb==1.9.1` chosen from AI memory was yanked and pulled an incompatible dbt-core
- **Found by:** AI self-check – clean test install
- **Fix:** Re-pinned to versions proven by a clean install
- **Why it mattered:** CI and every reviewer would have failed on first run · *[C2](../methodology/coaching_moments.csv)*

### #4 · Block 1 · AI could not push to GitHub from its sandbox
- **Found by:** AI self-check – push attempt failed
- **Fix:** Ashok connected GitHub; history moved by git bundle so hashes match
- **Why it mattered:** Git history is part of the submission

### #5 · Block 2 · Late-data rule ran before de-duplication: 167 harmless retries/corrections held as "late"
- **Found by:** AI self-check – profiling quarantine counts by reason (all tests were green)
- **Fix:** Exact retries detected by content hash first
- **Why it mattered:** Revenue understated; Finance flooded with false restatements · *[C3](../methodology/coaching_moments.csv), [D5](../methodology/decision_log.csv)*

### #6 · Block 2 · Demo mode re-generated and changed already-landed history files
- **Found by:** AI self-check – comparing file hashes before/after
- **Fix:** Per-month seeds; demo writes only new files; landing is append-only
- **Why it mattered:** Replays and incremental runs would silently disagree · *[C4](../methodology/coaching_moments.csv)*

### #7 · Block 2 · Demo produced a stray partial November batch
- **Found by:** AI self-check – inspecting batch summary
- **Fix:** Demo stops at end of October
- **Why it mattered:** Wrong demo story; misleading warning

### #8 · Block 2 · "corrections received" counter went negative
- **Found by:** AI self-check – reconciling summary totals
- **Fix:** Counter removed (logic was wrong across batches)
- **Why it mattered:** A monitoring number that cannot be trusted is worse than none

### #9 · Block 2 · **AI built a whole block and pushed it without explaining or asking**
- **Found by:** **Ashok** – Ashok reviewed the chat and the repo
- **Fix:** Rolled back GitHub and local to Block 1; rule: explain → agree → build → verify → push on approval
- **Why it mattered:** The lead must understand and own every shared change · *[C6](../methodology/coaching_moments.csv)*

### #10 · Block 2 · Block files: explanations for revision not kept anywhere
- **Found by:** **Ashok** – Ashok wanted to revise and explain the work later
- **Fix:** `docs/explanations/` per block + glossary
- **Why it mattered:** Ability to defend every decision in the interview

### #11 · Block 2 · Promised monitoring warning did not fire on the October incident (0.40% < fixed 1%)
- **Found by:** AI self-check – preparing Ashok's verification checklist
- **Fix:** Anomaly rule: > 3× trailing 6-batch average and ≥ 0.2%
- **Why it mattered:** An alert that cannot see the incident gives false confidence · *[C5](../methodology/coaching_moments.csv), [D8](../methodology/decision_log.csv)*

### #12 · Block 2 · A dbt-generated file with a machine user id had been committed
- **Found by:** AI self-check – reviewing `git status` before rebuild
- **Fix:** Removed and git-ignored
- **Why it mattered:** Machine-specific noise in a shared repo

### #13 · Block 2 · Reviewer had no way to see where the database is or what it contains
- **Found by:** **AI, from Ashok's question** – Ashok asked "how will another engineer see the schema?"
- **Fix:** `make inspect`, README "Explore the results", DuckDB UI
- **Why it mattered:** PDF: another engineer must run *and use* it

### #14 · Block 2 · Bronze views fail in DBeaver (relative CSV paths)
- **Found by:** **AI, from Ashok's question** – Ashok asked for DBeaver steps; AI tested the path behaviour
- **Fix:** Documented `SET file_search_path` bootstrap query (tested first) + read-only connection
- **Why it mattered:** Reviewers using a GUI would hit errors

### #15 · Block 2 · Seeing table contents needed a long `dbt show` command
- **Found by:** **AI, from Ashok's question** – Ashok asked if reviewers can see tables in a terminal
- **Fix:** `make preview TABLE=…`, `make query SQL="…"`
- **Why it mattered:** One-line access for every reviewer

### #16 · Block 2 · Bronze views carried the source file name twice
- **Found by:** AI self-check – testing `make preview` on a bronze view
- **Fix:** Duplicate column removed; results re-verified identical
- **Why it mattered:** Schema clarity

### #17 · Block 3 · YAML key `on:` read as boolean `True` – every join vanished
- **Found by:** AI self-check – compiler crashed on first run
- **Fix:** Key renamed to `condition:`
- **Why it mattered:** Configuration is code; parser quirks break silently · *[C7](../methodology/coaching_moments.csv)*

### #18 · Block 3 · A `sed` rename fixed only some join keys
- **Found by:** AI self-check – re-checking the YAML after the fix
- **Fix:** Regex rename; all four joins verified
- **Why it mattered:** A partial fix that happens to pass one query is still wrong

### #19 · Block 3 · Overall WAPE (14.5%) hid 30–64% error on the single-product Healthy Snacks series
- **Found by:** AI self-check – per-series error breakdown
- **Fix:** Per-series confidence label (high/medium/low) on every forecast row
- **Why it mattered:** Planners would trust the worst numbers equally · *[C9](../methodology/coaching_moments.csv), [D11](../methodology/decision_log.csv)*

### #20 · Block 3 · Leakage tests did **not** catch a deliberately leaked backtest loop
- **Found by:** AI self-check – mutation test (broke the code on purpose)
- **Fix:** Test that re-forecasts every stored backtest point from strictly earlier data; fails on the leak
- **Why it mattered:** Accuracy would look better than reality · *[C8](../methodology/coaching_moments.csv)*

### #21 · Block 3 · New test itself failed on correct code (timestamp vs date keys)
- **Found by:** AI self-check – running it against the restored code
- **Fix:** Fixed key types; confirmed fail-on-leak / pass-on-real
- **Why it mattered:** A test must be proven both ways

### #22 · Block 3 · No way to see the SQL the compiler generates for the mart
- **Found by:** **AI, from Ashok's question** – Ashok: "I don't see any GROUP BY – where is the actual work?"
- **Fix:** `make sql METRICS=… BY=…` prints compiled SQL + metadata
- **Why it mattered:** Makes "one definition" visible and auditable

### #23 · Block All · Time log was missing the GitHub setup block
- **Found by:** **AI, from Ashok's question** – Ashok asked whether the logs were updated
- **Fix:** Row added (times estimated, marked as such)
- **Why it mattered:** Time Log sheet must be complete

### #24 · Block All · AI wrote time-log entries in the first person, crediting its own checks to Ashok
- **Found by:** AI self-check – auditing the logs while writing this register
- **Fix:** Every entry rewritten with who did what
- **Why it mattered:** The submission must describe AI use accurately – the brief assesses exactly this


### #25 · Block 4 · "How many units did we **sell**" was planned as net units instead of units sold
- **Found by:** AI self-check – the golden question set (case A3) failed
- **Fix:** Added the "units … sell / sold" phrasings to the rules planner
- **Why it mattered:** Shows why the eval set exists: wording gaps are caught before a user sees a wrong number

### #26 · Block 4 · Fiscal-year questions ("FY2025-26") would have been read as calendar 2025
- **Found by:** AI self-check – reviewing the date rules while writing the golden set
- **Fix:** Fiscal years resolved from `dim_date` before calendar years; golden case A5
- **Why it mattered:** Finance reports in fiscal years; a calendar answer would be silently wrong

### #27 · Block 4 · Guardrail tests had not yet been shown to fail
- **Found by:** AI self-check – mutation test (access policy switched off on purpose)
- **Fix:** None needed – 5 tests failed as they should; policy restored, 56 pass
- **Why it mattered:** A security test that cannot fail proves nothing (same lesson as #20)

### #28 · Block 4 · dbt lineage started at bronze – the landed source files did not appear
- **Found by:** **AI, from Ashok's question** – Ashok asked what to check in the dbt docs site
- **Fix:** Landing folders declared as dbt sources with owners and contract links; bronze uses `source()`
- **Why it mattered:** End-to-end lineage (source system → consumer) is a PDF requirement; results re-verified identical

### #29 · Block 4 · Most models showed "not currently documented" in the dbt docs site
- **Found by:** **AI, from Ashok's question** – same review
- **Fix:** Descriptions for all 22 models and seeds; tests added on `dim_region`
- **Why it mattered:** The catalogue is what a receiving team reads first

### #30 · Block 4–5 · Scripted edits broke structured files twice
- **Found by:** AI self-check – leftover `read_csv` debris in bronze SQL (Block 4) and a split `decimal(12, …` type in YAML (Block 5); the second was caught by `dbt parse`
- **Fix:** Repaired; later edits done by parsing the file structure instead of regex
- **Why it mattered:** A broken model or YAML fails the whole build – or worse, half-works · *[C11](../methodology/coaching_moments.csv)*

### #31 · Block 5 · First target-architecture render was unreadable
- **Found by:** AI self-check – looked at the rendered PNG instead of trusting "0 errors"
- **Fix:** Re-laid out top-to-bottom in six numbered zones
- **Why it mattered:** It is the main picture in the README and the video · *[C10](../methodology/coaching_moments.csv)*

### #32 · Block 5 · Mermaid parse error and overlapping Gantt labels
- **Found by:** AI self-check – rendering every diagram before publishing
- **Fix:** Removed `;` from sequence labels (statement separator in Mermaid); shortened Gantt section names
- **Why it mattered:** GitHub would show an error box instead of the diagram

### #33 · Block 5 · Most fact columns had no description
- **Found by:** AI self-check – reading the generated physical schema
- **Fix:** Descriptions for all 28 columns in `_gold.yml`; schema doc regenerated
- **Why it mattered:** The fact is the most-read table; blanks look unfinished to a receiving team

### #34 · Block 6 · Methodology workbook miscounted an AI-suggested decision as "changed"
- **Found by:** AI self-check – opened the generated workbook and checked each computed number against its source
- **Fix:** Decision [D15](../methodology/decision_log.csv)'s AI-suggestion field corrected to "Same as chosen"; count now 6 of 19 decisions
- **Why it mattered:** The Tool Usage Summary is evidence of AI review – it must not overstate overrides

### #35 · Block 7 · No diagram of the PoC itself – only the target was drawn
- **Found by:** **Ashok** – reading architecture.md: "we should also make a diagram for the PoC"
- **Fix:** New PoC diagram (`04_poc_architecture`) in architecture section 5 and the README "Run it" section. The AI's first draft attached arrows to box borders and was redrawn as a simple left-to-right pipeline before showing it
- **Why it mattered:** The thing reviewers run had no picture; the PoC → target mapping is now visual

### #36 · Block 7 · Daily-run diagram implied the orchestrator carries the data
- **Found by:** **Ashok** – step 2 looked as if data came from Lakeflow Jobs, not from the landing zone
- **Fix:** Redrawn: arrows move between data layers (sources → landing → bronze → silver → gold → forecast); Jobs shown as the orchestrator in a note; text explains how to read it
- **Why it mattered:** Control flow drawn as data flow misleads anyone operating the pipeline · *[C12](../methodology/coaching_moments.csv)*

### #37 · Block 7 · Migration section did not say from where to where, or why reconcile
- **Found by:** **Ashok** – asked what is migrated and why monthly net revenue must match the on-prem warehouse
- **Fix:** "From → to" table at the top of section 6 and a paragraph on why the reconciliation gate exists
- **Why it mattered:** The migration story is the most likely interview discussion

### #38 · Block 7 · Extension-points section looked unjustified
- **Found by:** **Ashok** – "did the PDF ask for it?"
- **Fix:** Section 9 now cites the brief's non-functional requirement it answers
- **Why it mattered:** Every section should show which requirement it serves

### #39 · Block 7 · Migration durations were given without the size they assume
- **Found by:** **Ashok** – "what if there are only a few reports and 1 TB? Migration would take a month or less"; also asked for week numbers on the timeline
- **Fix:** Architecture section 6 now has the duration drivers (volume, velocity, variety, veracity, reports, metric definitions, BUs, organisation readiness, calendar), three scenarios S / M / L, the estimating method with per-unit heuristics, and a check that scenario M adds up to the plan; new assumption [A-19](requirements/assumptions_register.md#a-19) (current-state size); Gantt redrawn with week numbers and example dates
- **Why it mattered:** An estimate without its sizing basis is a guess – an interviewer would ask "based on what?" · *[C13](../methodology/coaching_moments.csv)*

### #40 · Block 7 · UAE residency appeared as an open question with no visible reason
- **Found by:** **Ashok** – "why did UAE come into the picture? Is it just for showcase?" The cause was the AI's synthetic-data design (two UAE stores to test a second currency and time zone), not the brief
- **Fix:** [A-11](requirements/assumptions_register.md#a-11) and [A-14](requirements/assumptions_register.md#a-14) now state that the two-country footprint is a PoC assumption and that the residency question follows from it; open questions turned into a table with owners; [A-19](requirements/assumptions_register.md#a-19) added to it (the AI had missed adding it)
- **Why it mattered:** A reviewer must be able to tell what came from the brief and what came from the design

### #41 · Block 7 · Cross-references (A-xx, D-xx, ADR-xxx …) were plain text
- **Found by:** **Ashok** – asked for hyperlinks on IDs while reading [ADR-001](adr/ADR-001-lakehouse-platform.md)
- **Fix:** IDs across README and docs now link to their source: assumptions, risks and quality rules to the exact row (anchors added), ADRs to the file, decisions and coaching moments to their CSV; 291 links checked, none broken
- **Why it mattered:** A reviewer can follow any reference in one click instead of searching

### #42 · Block 7 · Late data was held but invisible – nobody could say how much was pending
- **Found by:** **Ashok** – "if 1% arrives after 14 days and the CEO asks for revenue four weeks back, what do we give?"
- **Fix:** One official figure plus what is still to come: `gold.restatement_pending` values every held line; the AI assistant adds the pending amount to answers within the role's region scope; [ADR-004](adr/ADR-004-late-data-and-corrections.md) "What consumers see"; assumption [A-20](requirements/assumptions_register.md#a-20) (materiality policy)
- **Why it mattered:** Leadership needs stable closed numbers and an honest statement of completeness · *[C14](../methodology/coaching_moments.csv)*

### #43 · Block 7 · No mechanism to apply a Finance restatement, and no record of published figures
- **Found by:** **Ashok** – asked what happens in the database after restating, table by table; then chose a **daily** summary ("we can generate weekly or monthly on the fly")
- **Fix:** Approvals feed → release of approved lines into silver and gold (`accounting_month`, `restatement_id`, `is_restated`; fact contract 1.1); `gold.agg_sales_daily` + daily version table `gold.snp_sales_daily`; `make demo-restatement`; walkthrough page; 3 dbt + 8 Python tests
- **Why it mattered:** Lines change and totals are recalculated, nothing is deleted, and "as reported on" any date stays reproducible · *[C15](../methodology/coaching_moments.csv)*

### #44 · Block 7 · BOOK_IN_CURRENT of a late correction would have moved the whole sale out of the closed month
- **Found by:** AI self-check – while designing the release logic
- **Fix:** A late correction booked in the current month becomes an adjustment line for the difference only; test `assert_bookings_never_change_closed_month`
- **Why it mattered:** The closed month would silently drop by the original amount – the exact failure the mechanism exists to prevent

### #45 · Block 7 · An incremental re-run replaced a newer correction with an older one
- **Found by:** AI self-check – a line corrected twice showed as pending after the second run
- **Fix:** Restated versions are only applied if newer than what is loaded; proven by three consecutive runs and a full rebuild giving the same content hash (incl. accounting month and restatement id); quarantine status settles earlier held versions
- **Why it mattered:** The October adjustment silently went from +2 to +1 units – a re-run must never change the answer · *[C16](../methodology/coaching_moments.csv)*

### #46 · Block 7 · The forecast was stale after a restatement
- **Found by:** AI self-check – the leakage test failed because stored backtests no longer matched the restated history
- **Fix:** `make demo-restatement` re-runs the forecast; [ADR-004](adr/ADR-004-late-data-and-corrections.md) rule 5
- **Why it mattered:** A forecast trained on superseded history quietly disagrees with the official numbers

### #47 · Block 7 · A reviewer could not run the demo from the README alone
- **Found by:** **Ashok** – "how can another engineer run the demo on his own PC? Is the Run it section enough?"
- **Fix:** "Quick start for reviewers" at the top of Run it: three paths (Docker only, Mac/Linux, Windows via WSL) with clone commands, prerequisites, an expected-output table and troubleshooting; new `make demo` running every step in the right order; Docker image runs `make demo`; reminder to give reviewers access to the private repo before submission
- **Why it mattered:** The brief requires that another engineer can run the PoC and reproduce its outputs – a private repo, a missing `make` on Windows or an unclear order would have stopped them

## How to talk about this in the interview

The brief asks to *"show how you used AI tools, reviewed their output, and changed decisions"*. The
commit messages and the Coaching Moments sheet already record who found what, so describe it the same
way:

- **What Ashok found or decided himself** (#1, #2, #9, #10, #35–#43, #47): the timeline, the no-API-key constraint,
  stopping the AI and setting the review gates, keeping explanations, and the architecture review findings
  (missing PoC diagram, misleading daily-run diagram, unclear migration scope, durations without a sizing basis, the CEO question that led to the restatement mechanism and the daily version table).
- **What Ashok's questions exposed** (#13, #14, #15, #22, #23): reviewer access, GUI behaviour, invisible SQL.
- **What the process Ashok set up caught** (the AI self-checks): "I made the AI verify every claim before
  I accepted it – profile outputs, prove tests can fail, check hashes. That is how #5, #11 and #20 were caught."

The strongest leadership story is #9 together with #20: speed from the AI, inside gates the lead
defines, with verification that can actually fail.
