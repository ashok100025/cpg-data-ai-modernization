# ADR-004 – Late data and corrections: 14-day window + restatement queue

- **Status:** Proposed · **Date:** 2026-11-04
- **Decision owner:** Architect proposes the mechanism; Finance owns the window and the restatement process
- **Related:** [D20](../../methodology/decision_log.csv), [D21](../../methodology/decision_log.csv) · [D5](../../methodology/decision_log.csv), [D7](../../methodology/decision_log.csv), [D8](../../methodology/decision_log.csv) · assumptions [A-05](../requirements/assumptions_register.md#a-05), [A-20](../requirements/assumptions_register.md#a-20)

## Context
Sources retry (exact re-sends), correct (same key, new values) and send lines late (a store offline for
days). Finance needs closed periods to stay stable; operations need late sales to count as soon as possible.

## Options

| Option | Closed periods | Data loss | Operational load |
|---|---|---|---|
| A. Apply everything whenever it arrives | Change silently | None | Low – but numbers move after reporting |
| B. Reject anything late | Stable | **Yes** | Low – but sales disappear |
| **C. Accept within a window; hold the rest for restatement** | Stable, changed only on purpose | None – held with reason | Restatement queue to work |

## Decision
**Option C.** Every line is identified by its business key. **Exact retries** are recognised by a content
hash and collapsed first (never judged as late). **Corrections** replace the earlier version (latest
ingestion wins). Lines or corrections arriving **more than 14 days** after their batch period started are
**quarantined as `LATE_BEYOND_WINDOW`** for Finance's restatement process. Incremental runs must equal
a full rebuild.

## Consequences
- **+** No silent changes to closed months; no data dropped; every held row has a reason and is monitored.
- **+** Retry storms do not inflate revenue or flood the restatement queue (the rule-order bug found in the PoC, [C3](../../methodology/coaching_moments.csv)).
- **−** Valid late corrections wait for a restatement cycle.
- **−** The window is a business parameter that must be agreed and may differ by source.

## What consumers see (added after review – Ashok's question "what do we tell the CEO?")

**One official figure, plus what is still to come – never two competing numbers.**

> *"Net revenue for June: ₹X (official). A further ₹Y (z%) of late June sales is pending Finance restatement."*

- Official figures come from the fact and never change silently.
- `gold.restatement_pending` values every late line still waiting, by sale month, region, category and source.
- The AI assistant adds that note to every answer whose period has pending value, **within the role's region
  scope** (defined in `metrics.yml` as the completeness signal `pending_restatement`, owner Finance).

## What happens on restatement (added after review)

Finance records a decision per sale month and source in the **approvals feed** (`landing.restatements`):

| Decision | Typical use | Effect |
|---|---|---|
| `RESTATE` | above materiality ([A-20](../requirements/assumptions_register.md#a-20)) | Late lines (or corrected lines) enter the fact in their **own sale month**; that month's figure changes and gets a new version |
| `BOOK_IN_CURRENT` | below materiality | New late lines are booked in the **booking month**; a late **correction** of a line already counted becomes an **adjustment line for the difference only** – the closed month keeps its figure |

Rules that make it safe:
1. **Nothing is deleted** – landing, bronze and `slv_sales_conformed` stay append-only; the quarantine row stays, its
   status changes to `released` with the restatement id.
2. **Lines change, totals are recomputed** – released lines are inserted into `slv_sales` / `fct_sales_line` (tagged
   `restatement_id`, `accounting_month`, `is_restated`); the daily summary, weekly mart, metric views and AI answers
   are recalculated from the fact. No aggregate is ever edited.
3. **Every published figure keeps its versions** – `gold.agg_sales_daily` (sale date × accounting month × region ×
   category × channel, additive measures) is snapshotted every run into `gold.snp_sales_daily`; any period's
   "as reported on date X" is the sum of the versions valid at X.
4. **Only lines that arrived before the approval are released**; an older version never replaces a newer one;
   incremental runs equal a full rebuild.
5. **A restatement re-runs the forecast** – history changed, so the backtest and forecast must be recomputed
   (the leakage test detects a stale forecast).

Interactive walkthrough with two on-time sales and one late sale, table by table:
[`docs/explanations/restatement_walkthrough.html`](../explanations/restatement_walkthrough.html).

Demo: `make demo-restatement` (after `make all` and `make demo-incremental`) approves June POS (RESTATE) and August
e-commerce corrections (BOOK_IN_CURRENT in October) and prints before / after from the version table.

## Validation needed before production
1. Finance agrees the window per source and the close calendar.
2. Measure real lateness and correction rates per source during the Phase 1 parallel run.
3. Define the restatement process (who approves, how often, how replays are applied and audited) and the materiality threshold ([A-20](../requirements/assumptions_register.md#a-20)).
4. Price-only corrections: adjustment lines carry the quantity difference at the corrected price; a correction that changes only the price needs a value-adjustment field – confirm whether sources send such corrections.
