# Monitoring signals

What is measured on every run, the threshold, who is alerted and what they do. *PoC* = implemented here;
*Prod* = to implement in Phase 1 (WS6).

| Signal | Measured by | Threshold | Severity | Alert to | Runbook action | Status |
|---|---|---|---|---|---|---|
| **Quarantine anomaly** | `slv_dq_batch_summary` | > 3× trailing 6-batch avg and ≥ 0.2% per source | Warn | Data Platform on-call + source owner | Check top `dq_reason`; contact source; replay after fix | PoC ✅ (fires on October) |
| **Data tests / contract failure** | `dbt build` | any failure | Block | Data Platform on-call | Downstream stops; gold keeps last good version; fix + rerun | PoC ✅ |
| **Freshness** | max `ingested_at` per source vs schedule | POS/e-com > 26 h; masters > 35 days | Block for reporting SLA | On-call + source owner | Check feed; escalate to source owner | Prod |
| **Volume** | rows landed per batch vs trailing average | < 50% or > 200% | Warn | On-call | Check for partial or duplicated delivery | Prod (data in `slv_dq_batch_summary`) |
| **Schema drift** | new / missing columns in bronze | any new column; any missing required column | Warn / Block | Ingestion engineer | Additive: update contract version; missing: block, contact source | Prod |
| **Late rows held** | `late_rows_held` | > 0 | Info | Finance (restatement queue) | Include in restatement cycle | PoC ✅ (data) |
| **Master-data conflicts** | `slv_product_conflicts` | > 0 | Info | Master Data owner | Resolve in source system | PoC ✅ (data) |
| **Forecast accuracy drift** | WAPE of last 4 weeks vs backtest WAPE | > 1.5× backtest | Warn | Forecast owner + Planning | Investigate; re-select model; review confidence labels | Prod (backtest tables in PoC) |
| **AI refusal / restriction rate** | audit log status counts | refusal rate > 30% of a week's questions | Info | AI owner | Grow catalogue or planner phrasings; add golden cases | Prod (audit log in PoC) |
| **AI policy denials by role** | audit log `REFUSED_UNAUTHORIZED` | spike vs baseline | Warn | Data Governance | Check for misuse or wrong group mapping | Prod |
| **Pipeline duration** | job run time | > 1.5× median | Warn | On-call | Check volume, cluster, skew | Prod |
| **Cost** | Azure Cost Management by tag | > 80% of monthly budget | Warn | Pod lead + FinOps | Review warehouse auto-stop, job schedules | Prod |

## Principles
- Thresholds are **relative to a baseline** where possible (decision D8) and **proven to fire** on a known-bad case before go-live.
- Every alert names an **owner and a runbook action**; an alert nobody acts on is removed.
- Monitoring data lives in tables (queryable, testable), not only in dashboards.
