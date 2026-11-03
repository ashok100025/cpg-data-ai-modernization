-- Rows that failed a quality rule. Never silently dropped: held here with the reason,
-- surfaced in monitoring, and replayed after the source is fixed. LATE_BEYOND_WINDOW rows
-- go to Finance's restatement process instead of changing closed periods automatically.
select * from {{ ref('slv_sales_conformed') }} where dq_reason is not null
