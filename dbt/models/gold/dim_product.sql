-- Gold: product dimension, SCD type 2. A new version is created only when a tracked
-- attribute changes (brand, category, pack size, lifecycle status), so a category
-- reclassification does not rewrite history. Rebuilt deterministically from retained
-- monthly extracts (ADR-002); effective dates are the extract date (assumption A-08).
with h as (
    select sku, extract_date, product_name, brand_name, category_name, pack_size, launch_date, lifecycle_status,
           md5(concat_ws('|', brand_name, category_name, pack_size, lifecycle_status)) as attr_hash
    from {{ ref('slv_product_history') }}
    where in_erp and in_pim
),
chg as (
    select *, lag(attr_hash) over (partition by sku order by extract_date) as prev_hash from h
),
versions as (
    select *,
        row_number() over (partition by sku order by extract_date) as version_no,
        lead(extract_date) over (partition by sku order by extract_date) as next_from
    from chg where prev_hash is null or prev_hash <> attr_hash
)
select
    md5(sku || '|' || cast(extract_date as varchar))                       as product_sk,
    sku, product_name, brand_name, category_name, pack_size, launch_date, lifecycle_status,
    version_no,
    case when version_no = 1 then date '1900-01-01' else extract_date end  as valid_from,
    coalesce(next_from - 1, date '9999-12-31')                             as valid_to,
    next_from is null                                                      as is_current
from versions
