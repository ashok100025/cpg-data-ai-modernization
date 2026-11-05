# ADR-004 – Late data and corrections: 14-day window + restatement queue

- **Status:** Proposed · **Date:** 2026-11-04
- **Decision owner:** Architect proposes the mechanism; Finance owns the window and the restatement process
- **Related:** D5, D7, D8 · assumption A-05

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
- **+** Retry storms do not inflate revenue or flood the restatement queue (the rule-order bug found in the PoC, C3).
- **−** Valid late corrections wait for a restatement cycle.
- **−** The window is a business parameter that must be agreed and may differ by source.

## Validation needed before production
1. Finance agrees the window per source and the close calendar.
2. Measure real lateness and correction rates per source during the Phase 1 parallel run.
3. Define the restatement process (who approves, how often, how replays are applied and audited).
