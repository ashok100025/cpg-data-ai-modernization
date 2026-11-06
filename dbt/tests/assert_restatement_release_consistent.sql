-- ADR-004: a quarantined late line is 'released' if and only if it - or a later version of the same line - entered
-- slv_sales through a restatement; each original line has at most one restated row per kind (full / adjustment).
with released_in_silver as (
    select restated_line_key, max(ingested_at) as latest_released_at,
           count(*) filter (where sales_line_key = restated_line_key) as full_rows,
           count(*) filter (where sales_line_key <> restated_line_key) as adjustment_rows
    from {{ ref('slv_sales') }} where is_restated group by 1
),
q as (select * from {{ ref('slv_sales_quarantine') }} where dq_reason = 'LATE_BEYOND_WINDOW')
select 'released but no later released version in slv_sales' as problem, q.sales_line_key
from q left join released_in_silver r on q.sales_line_key = r.restated_line_key and q.ingested_at <= r.latest_released_at
where q.release_status = 'released' and r.restated_line_key is null
union all
select 'a later version is released but quarantine not marked released', q.sales_line_key
from q join released_in_silver r on q.sales_line_key = r.restated_line_key and q.ingested_at <= r.latest_released_at
where q.release_status <> 'released'
union all
select 'more than one restated row of one kind', restated_line_key from released_in_silver where full_rows > 1 or adjustment_rows > 1
