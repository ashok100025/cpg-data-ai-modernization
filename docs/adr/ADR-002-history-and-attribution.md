# ADR-002 – History: SCD2 dimensions, as-was reporting, as-is forecasting

- **Status:** Proposed · **Date:** 2026-11-04
- **Decision owner:** Architect proposes; Sales Operations (attribution) and Master Data (effective dates) confirm
- **Related:** D6, D10 · assumptions A-02, A-08, A-12

## Context
Product attributes change (category reclassification, pack size, discontinuation) and a store can be
reassigned to another region (S003: SOUTH → WEST on 1 Jul 2026). Reports must not silently change
history; planners need like-for-like views; sources send monthly full extracts without effective-from dates.

## Options

| Option | Reporting behaviour | Rebuild from scratch | Effort |
|---|---|---|---|
| A. Type 1 overwrite | History rewritten to today's attributes – closed regional numbers change | Yes | Lowest |
| B. dbt snapshots | SCD2, but history exists only from the day snapshots start running | **No** – a fresh environment has no history | Low |
| **C. SCD2 rebuilt from retained extracts** | As-was by default, as-is available | **Yes**, deterministically | Medium |
| D. Stamp attributes on the fact only | As-was only; no as-is | Yes | Low, but inflexible |

## Decision
**Option C.** Keep every monthly extract in bronze; build `dim_product` and `dim_store` as SCD2 with a
new version only when a tracked attribute changes; join facts to the version valid on the sale date
and stamp `region_code_at_sale` on the fact. Expose both **region / category (as-was)** and
**region_as_is / category_as_is** in the metric catalogue. **Reporting defaults to as-was; the
forecast uses as-is** because future sales happen in today's structure.

## Consequences
- **+** Closed reports never change when a store moves; planners still get like-for-like history.
- **+** Any environment can be rebuilt with full history (tests prove no overlaps and one current version).
- **−** Effective dates are only as precise as the extract cadence (month) until sources send effective-from (A-08).
- **−** Two regional views can confuse users – every answer and report states which one it uses.

## Validation needed before production
1. Sales Ops confirms as-was as the reporting default and which reports need as-is.
2. Master Data confirms whether effective-from dates can be sent; switch to them if so.
3. Reconcile one region's history before and after a real reassignment with Sales Ops.
