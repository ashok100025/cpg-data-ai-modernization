-- Product master per extract with survivorship rules (assumption A-03):
--   ERP owns identity, pack size, launch date, lifecycle status, description
--   PIM owns brand and category
-- Where both systems send an attribute and disagree, ERP wins and the conflict is
-- surfaced in slv_product_conflicts for the Master Data owner instead of being hidden.
with erp as (
    select material_id as sku, material_desc as product_name, pack_size as erp_pack_size,
           cast(launch_date as date) as launch_date, lifecycle_status,
           cast(extract_date as date) as extract_date
    from {{ ref('brz_erp_material') }}
),
pim as (
    select sku_code as sku, brand_name, category_name, pack_size as pim_pack_size,
           cast(extract_date as date) as extract_date
    from {{ ref('brz_pim_product') }}
)
select
    coalesce(erp.sku, pim.sku)                     as sku,
    coalesce(erp.extract_date, pim.extract_date)   as extract_date,
    erp.product_name,
    pim.brand_name,
    pim.category_name,
    erp.erp_pack_size                              as pack_size,
    erp.launch_date,
    erp.lifecycle_status,
    pim.pim_pack_size,
    erp.sku is not null                            as in_erp,
    pim.sku is not null                            as in_pim,
    (erp.sku is not null and pim.sku is not null
     and lower(replace(erp.erp_pack_size, ' ', '')) <> lower(replace(pim.pim_pack_size, ' ', ''))) as has_pack_size_conflict
from erp
full outer join pim on erp.sku = pim.sku and erp.extract_date = pim.extract_date
