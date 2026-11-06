{{ config(materialized='incremental', incremental_strategy='delete+insert', unique_key='sales_line_key') }}
-- Silver: valid, de-duplicated sales lines - one row per business key.
--   retries      -> identical versions collapse to one
--   corrections  -> latest ingested version wins and replaces the earlier one (delete+insert)
--   restatements -> a LATE_BEYOND_WINDOW line is released when Finance approves its sale month and source
--                   and it arrived before the approval (ADR-004):
--                   RESTATE          the line (or corrected line) goes into its own sale month
--                   BOOK_IN_CURRENT  a new late line is booked in the booking month; a late CORRECTION of a
--                                    line already counted becomes an ADJUSTMENT line for the difference only,
--                                    so the closed month keeps its original figure
with conformed as (select * from {{ ref('slv_sales_conformed') }}),
approvals as (select * from {{ ref('slv_restatement_approvals') }}),
prior_valid as (   -- latest valid version already counted for each key
    select sales_line_key, qty as prior_qty
    from conformed where dq_reason is null
    qualify row_number() over (partition by sales_line_key order by ingested_at desc, source_file desc) = 1
),
released as (
    select c.*, a.restatement_id, a.decision, a.booking_month, p.prior_qty
    from conformed c
    join approvals a
      on c.dq_reason = 'LATE_BEYOND_WINDOW'
     and strftime(c.event_date_local, '%Y-%m') = a.period
     and (a.source_system = 'ALL' or a.source_system = c.source_system)
     and c.ingested_at <= a.approved_at
    left join prior_valid p on c.sales_line_key = p.sales_line_key
    qualify row_number() over (partition by c.sales_line_key, c.row_hash order by a.approved_at) = 1
),
released_full as (
    select * exclude (prior_qty), sales_line_key as restated_line_key
    from released
    where not (decision = 'BOOK_IN_CURRENT' and prior_qty is not null)
),
released_adjustment as (
    select * exclude (prior_qty) replace (md5(sales_line_key || '|ADJ|' || restatement_id) as sales_line_key,
                                          qty - prior_qty as qty),
           sales_line_key as restated_line_key
    from released
    where decision = 'BOOK_IN_CURRENT' and prior_qty is not null and qty <> prior_qty
),
valid as (
    select *, cast(null as varchar) as restatement_id, cast(null as varchar) as decision,
           cast(null as varchar) as booking_month, cast(null as varchar) as restated_line_key
    from conformed
    where dq_reason is null
    {% if is_incremental() %}
      and ingested_at > (select max(ingested_at) from {{ this }} where restatement_id is null)
    {% endif %}
),
restated as (
    select * from released_full
    union all by name
    select * from released_adjustment
),
candidates as (
    select * from valid
    union all by name
    select * from restated r
    {% if is_incremental() %}
    -- only versions newer than what is already loaded for that key: an older version must never replace a newer one
    where not exists (select 1 from {{ this }} t where t.sales_line_key = r.sales_line_key and t.ingested_at >= r.ingested_at)
    {% endif %}
),
ranked as (
    select *,
        row_number() over (partition by sales_line_key order by ingested_at desc, source_file desc) as rn,
        count(*)     over (partition by sales_line_key)                                            as versions_in_load
    from candidates
)
select
    * exclude (rn, dq_reason, decision, booking_month),
    days_late > 0 as is_late_arrival,
    case when decision = 'BOOK_IN_CURRENT' then booking_month
         else strftime(event_date_local, '%Y-%m') end           as accounting_month,
    restatement_id is not null                                   as is_restated
from ranked where rn = 1
