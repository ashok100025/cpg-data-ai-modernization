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
| **Ashok** | #1, #2, #9, #10 |
| **AI, from Ashok's question** | #13, #14, #15, #22, #23, #28, #29 |
| AI self-check | #3–#8, #11, #12, #16–#21, #24–#27 |

## Corrections

### #1 · Block 0 · AI planned 2 weeks, the window in the brief
- **Found by:** **Ashok** – recruiter had asked for the earliest submission
- **Fix:** Re-planned to ~1 day in 9 fixed blocks with documented scope cuts
- **Why it mattered:** Real constraints come from stakeholders, not documents · *C1, D4*

### #2 · Block 0 · AI assumed an LLM API key was available
- **Found by:** **Ashok** – Ashok has only a chat subscription
- **Fix:** Pluggable LLM provider with an offline deterministic default
- **Why it mattered:** Reviewers must reproduce the AI part without keys · *D3*

### #3 · Block 1 · Version pin `dbt-duckdb==1.9.1` chosen from AI memory was yanked and pulled an incompatible dbt-core
- **Found by:** AI self-check – clean test install
- **Fix:** Re-pinned to versions proven by a clean install
- **Why it mattered:** CI and every reviewer would have failed on first run · *C2*

### #4 · Block 1 · AI could not push to GitHub from its sandbox
- **Found by:** AI self-check – push attempt failed
- **Fix:** Ashok connected GitHub; history moved by git bundle so hashes match
- **Why it mattered:** Git history is part of the submission

### #5 · Block 2 · Late-data rule ran before de-duplication: 167 harmless retries/corrections held as "late"
- **Found by:** AI self-check – profiling quarantine counts by reason (all tests were green)
- **Fix:** Exact retries detected by content hash first
- **Why it mattered:** Revenue understated; Finance flooded with false restatements · *C3, D5*

### #6 · Block 2 · Demo mode re-generated and changed already-landed history files
- **Found by:** AI self-check – comparing file hashes before/after
- **Fix:** Per-month seeds; demo writes only new files; landing is append-only
- **Why it mattered:** Replays and incremental runs would silently disagree · *C4*

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
- **Why it mattered:** The lead must understand and own every shared change · *C6*

### #10 · Block 2 · Block files: explanations for revision not kept anywhere
- **Found by:** **Ashok** – Ashok wanted to revise and explain the work later
- **Fix:** `docs/explanations/` per block + glossary
- **Why it mattered:** Ability to defend every decision in the interview

### #11 · Block 2 · Promised monitoring warning did not fire on the October incident (0.40% < fixed 1%)
- **Found by:** AI self-check – preparing Ashok's verification checklist
- **Fix:** Anomaly rule: > 3× trailing 6-batch average and ≥ 0.2%
- **Why it mattered:** An alert that cannot see the incident gives false confidence · *C5, D8*

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
- **Why it mattered:** Configuration is code; parser quirks break silently · *C7*

### #18 · Block 3 · A `sed` rename fixed only some join keys
- **Found by:** AI self-check – re-checking the YAML after the fix
- **Fix:** Regex rename; all four joins verified
- **Why it mattered:** A partial fix that happens to pass one query is still wrong

### #19 · Block 3 · Overall WAPE (14.5%) hid 30–64% error on the single-product Healthy Snacks series
- **Found by:** AI self-check – per-series error breakdown
- **Fix:** Per-series confidence label (high/medium/low) on every forecast row
- **Why it mattered:** Planners would trust the worst numbers equally · *C9, D11*

### #20 · Block 3 · Leakage tests did **not** catch a deliberately leaked backtest loop
- **Found by:** AI self-check – mutation test (broke the code on purpose)
- **Fix:** Test that re-forecasts every stored backtest point from strictly earlier data; fails on the leak
- **Why it mattered:** Accuracy would look better than reality · *C8*

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

## How to talk about this in the interview

The brief asks to *"show how you used AI tools, reviewed their output, and changed decisions"*. The
commit messages and the Coaching Moments sheet already record who found what, so describe it the same
way:

- **What Ashok found or decided himself** (#1, #2, #9, #10): the timeline, the no-API-key constraint,
  stopping the AI and setting the review gates, keeping explanations.
- **What Ashok's questions exposed** (#13, #14, #15, #22, #23): reviewer access, GUI behaviour, invisible SQL.
- **What the process Ashok set up caught** (the AI self-checks): "I made the AI verify every claim before
  I accepted it – profile outputs, prove tests can fail, check hashes. That is how #5, #11 and #20 were caught."

The strongest leadership story is #9 together with #20: speed from the AI, inside gates the lead
defines, with verification that can actually fail.
