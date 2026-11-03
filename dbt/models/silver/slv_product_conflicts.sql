-- Conflicts between ERP and PIM, latest extract only: a work queue for the Master Data owner.
select sku, extract_date, pack_size as erp_pack_size, pim_pack_size,
       case when not in_erp then 'MISSING_IN_ERP'
            when not in_pim then 'MISSING_IN_PIM'
            else 'PACK_SIZE_MISMATCH' end as conflict_type
from {{ ref('slv_product_history') }}
where extract_date = (select max(extract_date) from {{ ref('slv_product_history') }})
  and (has_pack_size_conflict or not in_erp or not in_pim)
