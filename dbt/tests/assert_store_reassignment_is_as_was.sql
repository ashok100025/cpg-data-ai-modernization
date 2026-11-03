-- Business rule (A-02): S003 moved SOUTH -> WEST on 2026-07-01. Sales keep the region at sale time.
select * from {{ ref('fct_sales_line') }}
where store_code = 'S003'
  and ((event_date_local <  date '2026-07-01' and region_code_at_sale <> 'SOUTH')
    or (event_date_local >= date '2026-07-01' and region_code_at_sale <> 'WEST'))
