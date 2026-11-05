-- Bronze: e-commerce order lines. union_by_name absorbs additive schema drift
-- (promo_code appears from batch 2026-05); missing columns arrive as NULL.
select
    * exclude (filename),
    regexp_extract(filename, 'batch=([0-9]{4}-[0-9]{2})', 1) as _batch,
    filename                                                 as _source_file
from {{ source('landing', 'ecom') }}
