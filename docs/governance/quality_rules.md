# Data quality rules

Every rule the pipeline enforces, where it runs, what happens when it fails, who owns it, and the test
that proves it works. Severity: **Block** = stop downstream, keep last good gold; **Quarantine** = hold the
row with a reason, continue; **Collapse** = handled automatically, counted; **Warn** = alert, continue.

## Row-level rules (silver – `slv_sales_conformed.dq_reason`)

| ID | Rule | Severity | Action | Owner | Enforced / proven by |
|---|---|---|---|---|---|
| <a id="dq-01"></a>[DQ-01](#dq-01) | Store code present | Quarantine `MISSING_STORE` | Source fix + replay | POS / Digital Commerce owner | `accepted_values` on `slv_sales_quarantine.dq_reason`; 22 rows in demo |
| <a id="dq-02"></a>[DQ-02](#dq-02) | SKU exists in the product master | Quarantine `UNKNOWN_SKU` | Master Data adds SKU or source fixes; replay | Master Data | 44 rows in demo |
| <a id="dq-03"></a>[DQ-03](#dq-03) | Price present and ≥ 0 | Quarantine `INVALID_PRICE` | Source fix + replay | Source owner | 22 rows in demo |
| <a id="dq-04"></a>[DQ-04](#dq-04) | Quantity a whole number ≠ 0 (accepts `"3.0"`) | Quarantine `INVALID_QTY` | Source fix | Source owner | `try_cast` logic; schema-drift batch 2025-11 passes |
| <a id="dq-05"></a>[DQ-05](#dq-05) | Timestamp parseable | Quarantine `INVALID_TIMESTAMP` | Source fix | Source owner | – (no faults injected) |
| <a id="dq-06"></a>[DQ-06](#dq-06) | Currency equals the store's currency | Quarantine `CURRENCY_MISMATCH` | Investigate store or source config | Sales Ops | – (no faults injected) |
| <a id="dq-07"></a>[DQ-07](#dq-07) | Arrives ≤ 14 days after its batch period starts ([A-05](../requirements/assumptions_register.md#a-05)) | Quarantine `LATE_BEYOND_WINDOW` | Finance restatement queue | Finance | 99 rows in demo; [ADR-004](../adr/ADR-004-late-data-and-corrections.md) |
| <a id="dq-08"></a>[DQ-08](#dq-08) | Exact retry of a line already received | Collapse | Counted in `exact_retries_collapsed` | Data Platform | content-hash detection; 672 collapsed |
| <a id="dq-09"></a>[DQ-09](#dq-09) | Correction of a line (same key, new values) | Collapse – latest ingested wins | Replaces earlier version | Data Platform | `slv_sales` delete+insert; incremental = full refresh |

## Table-level rules (dbt tests)

| ID | Rule | Severity | Owner | Test |
|---|---|---|---|---|
| <a id="dq-10"></a>[DQ-10](#dq-10) | One row per business key in silver and gold | Block | Data Platform | `unique` / `not_null` on `sales_line_key` |
| <a id="dq-11"></a>[DQ-11](#dq-11) | SCD2: no overlapping versions, exactly one current per key | Block | Modelling | `assert_scd2_no_overlap_and_one_current` |
| <a id="dq-12"></a>[DQ-12](#dq-12) | Gold reconciles to validated silver (rows, units) – no join fan-out | Block | Modelling | `assert_fact_reconciles_to_silver` |
| <a id="dq-13"></a>[DQ-13](#dq-13) | Every fact row links to date, store and product | Block | Modelling | `relationships` tests |
| <a id="dq-14"></a>[DQ-14](#dq-14) | Channel, type, source system have allowed values | Block | Modelling | `accepted_values` |
| <a id="dq-15"></a>[DQ-15](#dq-15) | Fact columns and types match the published contract | Block | Modelling (contract owner) | dbt model contract (enforced) |
| <a id="dq-16"></a>[DQ-16](#dq-16) | As-was attribution: S003 in SOUTH before 1 Jul 2026, WEST after | Block | Modelling / Sales Ops | `assert_store_reassignment_is_as_was` |
| <a id="dq-17"></a>[DQ-17](#dq-17) | Mart totals equal fact totals; one row per mart grain | Block | Metrics | `assert_mart_reconciles_to_fact`, `unique_mart_grain` |
| <a id="dq-18"></a>[DQ-18](#dq-18) | Batch quarantine rate > 3× trailing 6-batch average **and** ≥ 0.2% | **Warn** | Data Platform on-call | `assert_quarantine_rate_below_threshold` (fires on October) |
| <a id="dq-19"></a>[DQ-19](#dq-19) | ERP vs PIM attribute conflicts published, not hidden | Warn (work queue) | Master Data | `slv_product_conflicts` |
| <a id="dq-20"></a>[DQ-20](#dq-20) | Additive schema drift absorbed; breaking drift fails typed silver | Collapse / Block | Data Platform | text-first bronze + `union_by_name`; typed casts in silver |

## Restatement rules ([ADR-004](../adr/ADR-004-late-data-and-corrections.md))

| ID | Rule | Severity | Owner | Test |
|---|---|---|---|---|
| <a id="dq-25"></a>[DQ-25](#dq-25) | A late line is released only by a Finance approval for its sale month and source, and only if it arrived before the approval | Block | Finance / Data Platform | `slv_sales` release logic; `test_restated_lines_and_closed_months` |
| <a id="dq-26"></a>[DQ-26](#dq-26) | Released ⇔ in `slv_sales`; each original line restated at most once per kind; nothing deleted from quarantine; an older version never replaces a newer one | Block | Data Platform | `assert_restatement_release_consistent`, `test_quarantine_keeps_every_late_line`; incremental = full rebuild |
| <a id="dq-27"></a>[DQ-27](#dq-27) | BOOK_IN_CURRENT never changes the closed sale month (adjustment lines for corrections) | Block | Finance | `assert_bookings_never_change_closed_month`, `test_book_in_current_leaves_closed_month_unchanged` |
| <a id="dq-28"></a>[DQ-28](#dq-28) | Daily summary reconciles to the fact; any month derived from it equals the fact | Block | Metrics | `assert_daily_summary_reconciles_to_fact`, `test_daily_summary_rolls_up_to_any_period` |
| <a id="dq-29"></a>[DQ-29](#dq-29) | Pending value equals unreleased late lines; AI notes show it within the role's region scope | Block (CI) | Finance / AI owner | `test_pending_view_equals_unreleased_late_lines`, `test_pending_note_respects_the_role_region_scope` |

## Semantic and AI rules (Python tests)

| ID | Rule | Severity | Test |
|---|---|---|---|
| <a id="dq-21"></a>[DQ-21](#dq-21) | Metric totals equal fact totals through every dimension | Block (CI) | `test_totals_equal_fact_through_every_dimension` |
| <a id="dq-22"></a>[DQ-22](#dq-22) | Unknown metrics, dimensions, filters refused | Block (CI) | `test_refuses_anything_not_in_catalogue` |
| <a id="dq-23"></a>[DQ-23](#dq-23) | Forecast backtest uses only data before each origin | Block (CI) | `test_stored_backtest_used_only_data_before_each_origin` |
| <a id="dq-24"></a>[DQ-24](#dq-24) | AI answers only allowed metrics / rows; refusals as specified | Block (CI) | `tests/insight_eval.yml` (19 cases), malicious-planner tests |

## Principles
- **Never silently drop** a row: it is valid, collapsed (counted) or quarantined (with a reason).
- **Prove each rule can fail**: injected faults in the synthetic data exercise [DQ-01](#dq-01)…[DQ-09](#dq-09); mutation tests exercised [DQ-23](#dq-23) and [DQ-24](#dq-24).
- **Thresholds come from baselines**, not guesses ([DQ-18](#dq-18) – decision [D8](../../methodology/decision_log.csv)).
