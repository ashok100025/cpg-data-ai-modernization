-- Rows that failed a quality rule. Never deleted: held here with the reason, surfaced in monitoring and
-- replayed after the source is fixed. LATE_BEYOND_WINDOW rows wait for Finance: release_status turns
-- 'released' (with the restatement id) once an approval releases them - or a later version of the same line -
-- into slv_sales (ADR-004).
with q as (
    select * from {{ ref('slv_sales_conformed') }} where dq_reason is not null
),
released as (   -- latest released version per original line (a release also settles any earlier held version)
    select restated_line_key as sales_line_key, ingested_at as released_version_ingested_at, restatement_id
    from {{ ref('slv_sales') }} where is_restated
    qualify row_number() over (partition by restated_line_key order by ingested_at desc) = 1
)
select
    q.*,
    cast(round(q.qty * q.unit_price * fx.rate_to_inr, 2) as decimal(14, 2))   as value_inr,
    case when r.sales_line_key is not null then 'released'
         when q.dq_reason = 'LATE_BEYOND_WINDOW' then 'pending_restatement'
         else 'held_for_source_fix' end                                         as release_status,
    r.restatement_id
from q
left join released r on q.sales_line_key = r.sales_line_key and q.ingested_at <= r.released_version_ingested_at
left join {{ ref('fx_rates_monthly') }} fx
       on cast(date_trunc('month', q.event_date_local) as date) = fx.month_start and q.currency_code = fx.currency_code
