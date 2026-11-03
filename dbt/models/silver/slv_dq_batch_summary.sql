-- Monitoring signal per batch and source: what landed, what passed, what was held and why.
select
    batch_id, source_system,
    count(*)                                                    as rows_landed,
    count(*) filter (where dq_reason is null)                  as rows_valid,
    count(*) filter (where dq_reason is not null)              as rows_quarantined,
    count(*) filter (where is_exact_retry)                     as exact_retries_collapsed,
    count(*) filter (where days_late > 0 and dq_reason is null) as late_rows_accepted,
    count(*) filter (where dq_reason = 'LATE_BEYOND_WINDOW')   as late_rows_held,
    count(*) filter (where dq_reason = 'UNKNOWN_SKU')          as unknown_sku,
    count(*) filter (where dq_reason = 'INVALID_PRICE')        as invalid_price,
    count(*) filter (where dq_reason = 'MISSING_STORE')        as missing_store,
    round(100.0 * count(*) filter (where dq_reason is not null) / count(*), 3) as pct_quarantined
from {{ ref('slv_sales_conformed') }}
group by 1, 2
