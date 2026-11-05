# Data quality rules

Every rule the pipeline enforces, where it runs, what happens when it fails, who owns it, and the test
that proves it works. Severity: **Block** = stop downstream, keep last good gold; **Quarantine** = hold the
row with a reason, continue; **Collapse** = handled automatically, counted; **Warn** = alert, continue.

## Row-level rules (silver – `slv_sales_conformed.dq_reason`)

| ID | Rule | Severity | Action | Owner | Enforced / proven by |
|---|---|---|---|---|---|
| DQ-01 | Store code present | Quarantine `MISSING_STORE` | Source fix + replay | POS / Digital Commerce owner | `accepted_values` on `slv_sales_quarantine.dq_reason`; 22 rows in demo |
| DQ-02 | SKU exists in the product master | Quarantine `UNKNOWN_SKU` | Master Data adds SKU or source fixes; replay | Master Data | 44 rows in demo |
| DQ-03 | Price present and ≥ 0 | Quarantine `INVALID_PRICE` | Source fix + replay | Source owner | 22 rows in demo |
| DQ-04 | Quantity a whole number ≠ 0 (accepts `"3.0"`) | Quarantine `INVALID_QTY` | Source fix | Source owner | `try_cast` logic; schema-drift batch 2025-11 passes |
| DQ-05 | Timestamp parseable | Quarantine `INVALID_TIMESTAMP` | Source fix | Source owner | – (no faults injected) |
| DQ-06 | Currency equals the store's currency | Quarantine `CURRENCY_MISMATCH` | Investigate store or source config | Sales Ops | – (no faults injected) |
| DQ-07 | Arrives ≤ 14 days after its batch period starts (A-05) | Quarantine `LATE_BEYOND_WINDOW` | Finance restatement queue | Finance | 99 rows in demo; ADR-004 |
| DQ-08 | Exact retry of a line already received | Collapse | Counted in `exact_retries_collapsed` | Data Platform | content-hash detection; 672 collapsed |
| DQ-09 | Correction of a line (same key, new values) | Collapse – latest ingested wins | Replaces earlier version | Data Platform | `slv_sales` delete+insert; incremental = full refresh |

## Table-level rules (dbt tests)

| ID | Rule | Severity | Owner | Test |
|---|---|---|---|---|
| DQ-10 | One row per business key in silver and gold | Block | Data Platform | `unique` / `not_null` on `sales_line_key` |
| DQ-11 | SCD2: no overlapping versions, exactly one current per key | Block | Modelling | `assert_scd2_no_overlap_and_one_current` |
| DQ-12 | Gold reconciles to validated silver (rows, units) – no join fan-out | Block | Modelling | `assert_fact_reconciles_to_silver` |
| DQ-13 | Every fact row links to date, store and product | Block | Modelling | `relationships` tests |
| DQ-14 | Channel, type, source system have allowed values | Block | Modelling | `accepted_values` |
| DQ-15 | Fact columns and types match the published contract | Block | Modelling (contract owner) | dbt model contract (enforced) |
| DQ-16 | As-was attribution: S003 in SOUTH before 1 Jul 2026, WEST after | Block | Modelling / Sales Ops | `assert_store_reassignment_is_as_was` |
| DQ-17 | Mart totals equal fact totals; one row per mart grain | Block | Metrics | `assert_mart_reconciles_to_fact`, `unique_mart_grain` |
| DQ-18 | Batch quarantine rate > 3× trailing 6-batch average **and** ≥ 0.2% | **Warn** | Data Platform on-call | `assert_quarantine_rate_below_threshold` (fires on October) |
| DQ-19 | ERP vs PIM attribute conflicts published, not hidden | Warn (work queue) | Master Data | `slv_product_conflicts` |
| DQ-20 | Additive schema drift absorbed; breaking drift fails typed silver | Collapse / Block | Data Platform | text-first bronze + `union_by_name`; typed casts in silver |

## Semantic and AI rules (Python tests)

| ID | Rule | Severity | Test |
|---|---|---|---|
| DQ-21 | Metric totals equal fact totals through every dimension | Block (CI) | `test_totals_equal_fact_through_every_dimension` |
| DQ-22 | Unknown metrics, dimensions, filters refused | Block (CI) | `test_refuses_anything_not_in_catalogue` |
| DQ-23 | Forecast backtest uses only data before each origin | Block (CI) | `test_stored_backtest_used_only_data_before_each_origin` |
| DQ-24 | AI answers only allowed metrics / rows; refusals as specified | Block (CI) | `tests/insight_eval.yml` (19 cases), malicious-planner tests |

## Principles
- **Never silently drop** a row: it is valid, collapsed (counted) or quarantined (with a reason).
- **Prove each rule can fail**: injected faults in the synthetic data exercise DQ-01…DQ-09; mutation tests exercised DQ-23 and DQ-24.
- **Thresholds come from baselines**, not guesses (DQ-18 – decision D8).
