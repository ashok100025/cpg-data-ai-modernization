-- Gold: late lines waiting for a Finance decision, valued in INR - the "how much is still to come" signal
-- shown next to official figures (ADR-004). Released lines drop out; nothing is deleted from quarantine.
select
    strftime(q.event_date_local, '%Y-%m')        as event_month,
    st.region_code                               as region,
    p.category_name                              as category,
    q.source_system,
    count(*)                                     as pending_lines,
    sum(q.value_inr)                             as pending_inr,
    min(q.ingested_at)                           as first_arrived_at,
    max(q.ingested_at)                           as last_arrived_at
from {{ ref('slv_sales_quarantine') }} q
left join {{ ref('dim_store') }} st
       on q.store_code = st.store_code and q.event_date_local between st.valid_from and st.valid_to
left join {{ ref('dim_product') }} p
       on q.sku = p.sku and q.event_date_local between p.valid_from and p.valid_to
where q.release_status = 'pending_restatement'
group by all
