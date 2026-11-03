{{ config(severity='warn', warn_if='>0') }}
-- Monitoring gate (anomaly, not a fixed limit): warn when a batch quarantines more than 3x the
-- trailing 6-batch average for the same source AND at least 0.2% of its rows (floor avoids noise
-- on tiny percentages). Normal batches sit at 0.04-0.19%; a source incident shows as a spike.
with s as (
    select *,
        avg(pct_quarantined) over (partition by source_system order by batch_id
                                   rows between 6 preceding and 1 preceding) as trailing_avg_pct
    from {{ ref('slv_dq_batch_summary') }}
)
select batch_id, source_system, rows_landed, rows_quarantined, pct_quarantined, round(trailing_avg_pct, 3) as trailing_avg_pct
from s
where pct_quarantined > 3 * trailing_avg_pct and pct_quarantined >= 0.2
