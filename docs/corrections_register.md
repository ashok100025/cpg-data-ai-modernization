# Corrections register

Every problem found in AI-generated plans, code or documents during this case study, how it was
found, who spotted it, and what was changed. Kept alongside the methodology spreadsheet (Coaching
Moments, Decision Log) and the git history, and consistent with both.

**Spotted by** – *Ashok*: found or demanded by the candidate. *AI self-check*: found by the AI while
verifying its own work, inside the review process Ashok set (explain → agree → build → verify → push).
*AI, from Ashok's question*: Ashok's question exposed the gap; the AI found the cause and proposed the fix.

| # | Block | Problem found | How it was found | Spotted by | Correction | Why it mattered | Ref |
|---|---|---|---|---|---|---|---|
| 1 | 0 | AI planned 2 weeks, the window in the brief | Recruiter had asked for the earliest submission | **Ashok** | Re-planned to ~1 day in 9 fixed blocks with documented scope cuts | Real constraints come from stakeholders, not documents | C1, D4 |
| 2 | 0 | AI assumed an LLM API key was available | Ashok has only a chat subscription | **Ashok** | Pluggable LLM provider with an offline deterministic default | Reviewers must reproduce the AI part without keys | D3 |
| 3 | 1 | Version pin `dbt-duckdb==1.9.1` chosen from AI memory was yanked and pulled an incompatible dbt-core | Clean test install | AI self-check | Re-pinned to versions proven by a clean install | CI and every reviewer would have failed on first run | C2 |
| 4 | 1 | AI could not push to GitHub from its sandbox | Push attempt failed | AI self-check | Ashok connected GitHub; history moved by git bundle so hashes match | Git history is part of the submission | – |
| 5 | 2 | Late-data rule ran before de-duplication: 167 harmless retries/corrections held as "late" | Profiling quarantine counts by reason – all tests were green | AI self-check | Exact retries detected by content hash first | Revenue understated; Finance flooded with false restatements | C3, D5 |
| 6 | 2 | Demo mode re-generated and changed already-landed history files | Comparing file hashes before/after | AI self-check | Per-month seeds; demo writes only new files; landing is append-only | Replays and incremental runs would silently disagree | C4 |
| 7 | 2 | Demo produced a stray partial November batch | Inspecting batch summary | AI self-check | Demo stops at end of October | Wrong demo story; misleading warning | – |
| 8 | 2 | "corrections received" counter went negative | Reconciling summary totals | AI self-check | Counter removed (logic was wrong across batches) | A monitoring number that cannot be trusted is worse than none | – |
| 9 | 2 | **AI built a whole block and pushed it without explaining or asking** | Ashok reviewed the chat and the repo | **Ashok** | Rolled back GitHub and local to Block 1; rule: explain → agree → build → verify → push on approval | The lead must understand and own every shared change | C6 |
| 10 | 2 | Block files: explanations for revision not kept anywhere | Ashok wanted to revise and explain the work later | **Ashok** | `docs/explanations/` per block + glossary | Ability to defend every decision in the interview | – |
| 11 | 2 | Promised monitoring warning did not fire on the October incident (0.40% < fixed 1%) | Preparing Ashok's verification checklist | AI self-check | Anomaly rule: > 3× trailing 6-batch average and ≥ 0.2% | An alert that cannot see the incident gives false confidence | C5, D8 |
| 12 | 2 | A dbt-generated file with a machine user id had been committed | Reviewing `git status` before rebuild | AI self-check | Removed and git-ignored | Machine-specific noise in a shared repo | – |
| 13 | 2 | Reviewer had no way to see where the database is or what it contains | Ashok asked "how will another engineer see the schema?" | **AI, from Ashok's question** | `make inspect`, README "Explore the results", DuckDB UI | PDF: another engineer must run *and use* it | – |
| 14 | 2 | Bronze views fail in DBeaver (relative CSV paths) | Ashok asked for DBeaver steps; AI tested the path behaviour | **AI, from Ashok's question** | Documented `SET file_search_path` bootstrap query (tested first) + read-only connection | Reviewers using a GUI would hit errors | – |
| 15 | 2 | Seeing table contents needed a long `dbt show` command | Ashok asked if reviewers can see tables in a terminal | **AI, from Ashok's question** | `make preview TABLE=…`, `make query SQL="…"` | One-line access for every reviewer | – |
| 16 | 2 | Bronze views carried the source file name twice | Testing `make preview` on a bronze view | AI self-check | Duplicate column removed; results re-verified identical | Schema clarity | – |
| 17 | 3 | YAML key `on:` read as boolean `True` – every join vanished | Compiler crashed on first run | AI self-check | Key renamed to `condition:` | Configuration is code; parser quirks break silently | C7 |
| 18 | 3 | A `sed` rename fixed only some join keys | Re-checking the YAML after the fix | AI self-check | Regex rename; all four joins verified | A partial fix that happens to pass one query is still wrong | – |
| 19 | 3 | Overall WAPE (14.5%) hid 30–64% error on the single-product Healthy Snacks series | Per-series error breakdown | AI self-check | Per-series confidence label (high/medium/low) on every forecast row | Planners would trust the worst numbers equally | C9, D11 |
| 20 | 3 | Leakage tests did **not** catch a deliberately leaked backtest loop | Mutation test – broke the code on purpose | AI self-check | Test that re-forecasts every stored backtest point from strictly earlier data; fails on the leak | Accuracy would look better than reality | C8 |
| 21 | 3 | New test itself failed on correct code (timestamp vs date keys) | Running it against the restored code | AI self-check | Fixed key types; confirmed fail-on-leak / pass-on-real | A test must be proven both ways | – |
| 22 | 3 | No way to see the SQL the compiler generates for the mart | Ashok: "I don't see any GROUP BY – where is the actual work?" | **AI, from Ashok's question** | `make sql METRICS=… BY=…` prints compiled SQL + metadata | Makes "one definition" visible and auditable | – |
| 23 | All | Time log was missing the GitHub setup block | Ashok asked whether the logs were updated | **AI, from Ashok's question** | Row added (times estimated, marked as such) | Time Log sheet must be complete | – |
| 24 | All | AI wrote time-log entries in the first person, crediting its own checks to Ashok | Auditing the logs while writing this register | AI self-check | Every entry rewritten with who did what | The submission must describe AI use accurately – the brief assesses exactly this | – |

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
