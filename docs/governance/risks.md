# Risks and failure scenarios

Likelihood / impact: H / M / L. Detection and recovery reference the monitoring signals and CI/CD notes.

| ID | Scenario | L | I | Detection | Mitigation (prevent) | Recovery | Owner |
|---|---|---|---|---|---|---|---|
| <a id="r-01"></a>[R-01](#r-01) | **Source outage** – a store's POS stops sending for days | M | M | Freshness, volume signals | Contracts with SLAs; late window | Late lines accepted ≤ 14 days; beyond → restatement | Source owner / on-call |
| <a id="r-02"></a>[R-02](#r-02) | **Retry storm** – gateway re-sends a day's lines | M | H | `exact_retries_collapsed` spike | Content-hash de-duplication before late rule ([C3](../../methodology/coaching_moments.csv)) | Automatic; verify counts | Data Platform |
| <a id="r-03"></a>[R-03](#r-03) | **Breaking schema change** without notice | M | H | Schema-drift signal; typed silver fails | Contract change policy, 30-day notice | Bronze keeps raw; fix mapping; replay | Ingestion engineer |
| <a id="r-04"></a>[R-04](#r-04) | **Wrong FX rate** loaded | L | H | Reconciliation vs Treasury; FX range check | Rates from Treasury feed, reviewed monthly | Correct seed/feed; rebuild gold (deterministic) | Finance |
| <a id="r-05"></a>[R-05](#r-05) | **Store mapped to wrong region** | M | M | Sales Ops review; as-was test | SCD2 with effective dates; owner approval on store master | Correct master; rebuild dims; restatement if closed | Sales Ops |
| <a id="r-06"></a>[R-06](#r-06) | **Metric definition dispute** between business units | H | H | Two reports disagree | One catalogue; metric owner per measure; forum (pod plan) | Decide in forum; rename variants – never two meanings for one name | Finance (metric owner) |
| <a id="r-07"></a>[R-07](#r-07) | **Prompt injection / data exfiltration** through the assistant | M | H | Refusal and denial rates; audit | LLM never sees data; deterministic guardrails; deny by default | Disable assistant (feature flag); review audit | Data Governance / AI owner |
| <a id="r-08"></a>[R-08](#r-08) | **Assistant gives a wrong but plausible answer** | M | H | Golden set in CI; user feedback | Only certified metrics; answer shows SQL, owner, freshness, caveats | Fix planner; add golden case | AI owner |
| <a id="r-09"></a>[R-09](#r-09) | **Forecast trusted beyond its accuracy** | M | M | Accuracy drift signal | Confidence label on every row; backtest published | Re-select model; communicate low-confidence series | Forecast owner |
| <a id="r-10"></a>[R-10](#r-10) | **Cost overrun** | M | M | Budget alert at 80% | Serverless auto-stop, job compute, tags, budgets | Scale down; review schedules | Pod lead / FinOps |
| <a id="r-11"></a>[R-11](#r-11) | **Reconciliation with on-prem warehouse fails** at the P1 gate | M | H | Reconciliation report | Parallel run; explain every difference by rule (assumptions) | Fix rule or agree difference with Finance before cut-over | Architect / Finance |
| <a id="r-12"></a>[R-12](#r-12) | **Key-person dependency** in a 3-engineer pod | M | M | – | Pairing, docs (`docs/explanations/`), ADRs, CODEOWNERS with two reviewers | Cross-trained second owner per workstream | Pod lead |
| <a id="r-13"></a>[R-13](#r-13) | **Bad deploy** corrupts gold | L | H | Tests in CI/test environment; post-deploy checks | Gates before prod; contract enforcement | Redeploy previous bundle; Delta `RESTORE` (cicd.md) | Platform engineer |
| <a id="r-14"></a>[R-14](#r-14) | **Data residency** for the second country (UAE in the PoC's two-country assumption) blocks central processing ([A-14](../requirements/assumptions_register.md#a-14)) | M | H | Legal review in P0 | Raise early; design allows a regional workspace | Split processing; aggregate-only transfer | Legal / Architect |
