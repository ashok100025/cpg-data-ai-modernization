{{ config(materialized='incremental', incremental_strategy='delete+insert', unique_key='sales_line_key') }}
-- Silver: valid, de-duplicated sales lines. One row per source line (the business key).
--   retries     -> identical versions collapse to one
--   corrections -> latest ingested version wins and replaces the earlier one (delete+insert)
with src as (
    select * from {{ ref('slv_sales_conformed') }}
    where dq_reason is null
    {% if is_incremental() %}
      and ingested_at > (select max(ingested_at) from {{ this }})
    {% endif %}
),
ranked as (
    select *,
        row_number() over (partition by sales_line_key order by ingested_at desc, source_file desc) as rn,
        count(*)     over (partition by sales_line_key)                                            as versions_in_load
    from src
)
select * exclude (rn, dq_reason), days_late > 0 as is_late_arrival
from ranked where rn = 1
