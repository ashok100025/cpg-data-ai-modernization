# Risks and failure scenarios

Likelihood / impact: H / M / L. Detection and recovery reference the monitoring signals and CI/CD notes.

| ID | Scenario | L | I | Detection | Mitigation (prevent) | Recovery | Owner |
|---|---|---|---|---|---|---|---|
| R-01 | **Source outage** – a store's POS stops sending for days | M | M | Freshness, volume signals | Contracts with SLAs; late window | Late lines accepted ≤ 14 days; beyond → restatement | Source owner / on-call |
| R-02 | **Retry storm** – gateway re-sends a day's lines | M | H | `exact_retries_collapsed` spike | Content-hash de-duplication before late rule (C3) | Automatic; verify counts | Data Platform |
| R-03 | **Breaking schema change** without notice | M | H | Schema-drift signal; typed silver fails | Contract change policy, 30-day notice | Bronze keeps raw; fix mapping; replay | Ingestion engineer |
| R-04 | **Wrong FX rate** loaded | L | H | Reconciliation vs Treasury; FX range check | Rates from Treasury feed, reviewed monthly | Correct seed/feed; rebuild gold (deterministic) | Finance |
| R-05 | **Store mapped to wrong region** | M | M | Sales Ops review; as-was test | SCD2 with effective dates; owner approval on store master | Correct master; rebuild dims; restatement if closed | Sales Ops |
| R-06 | **Metric definition dispute** between business units | H | H | Two reports disagree | One catalogue; metric owner per measure; forum (pod plan) | Decide in forum; rename variants – never two meanings for one name | Finance (metric owner) |
| R-07 | **Prompt injection / data exfiltration** through the assistant | M | H | Refusal and denial rates; audit | LLM never sees data; deterministic guardrails; deny by default | Disable assistant (feature flag); review audit | Data Governance / AI owner |
| R-08 | **Assistant gives a wrong but plausible answer** | M | H | Golden set in CI; user feedback | Only certified metrics; answer shows SQL, owner, freshness, caveats | Fix planner; add golden case | AI owner |
| R-09 | **Forecast trusted beyond its accuracy** | M | M | Accuracy drift signal | Confidence label on every row; backtest published | Re-select model; communicate low-confidence series | Forecast owner |
| R-10 | **Cost overrun** | M | M | Budget alert at 80% | Serverless auto-stop, job compute, tags, budgets | Scale down; review schedules | Pod lead / FinOps |
| R-11 | **Reconciliation with on-prem warehouse fails** at the P1 gate | M | H | Reconciliation report | Parallel run; explain every difference by rule (assumptions) | Fix rule or agree difference with Finance before cut-over | Architect / Finance |
| R-12 | **Key-person dependency** in a 3-engineer pod | M | M | – | Pairing, docs (`docs/explanations/`), ADRs, CODEOWNERS with two reviewers | Cross-trained second owner per workstream | Pod lead |
| R-13 | **Bad deploy** corrupts gold | L | H | Tests in CI/test environment; post-deploy checks | Gates before prod; contract enforcement | Redeploy previous bundle; Delta `RESTORE` (cicd.md) | Platform engineer |
| R-14 | **UAE data residency** blocks central processing (A-14) | M | H | Legal review in P0 | Raise early; design allows a regional workspace | Split processing; aggregate-only transfer | Legal / Architect |
