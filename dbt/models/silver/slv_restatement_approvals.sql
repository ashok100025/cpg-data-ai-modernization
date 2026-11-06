-- Silver: typed Finance approvals; one row per restatement id (a re-sent approval keeps the first one).
with a as (
    select
        restatement_id,
        period,                                               -- sale month the approval covers (YYYY-MM)
        upper(coalesce(nullif(source_system, ''), 'ALL'))      as source_system,
        upper(decision)                                        as decision,
        nullif(booking_month, '')                              as booking_month,
        approved_by,
        cast(approved_at as timestamp)                         as approved_at,
        note,
        row_number() over (partition by restatement_id order by approved_at) as rn
    from {{ ref('brz_restatement_approvals') }}
)
select * exclude (rn) from a where rn = 1
