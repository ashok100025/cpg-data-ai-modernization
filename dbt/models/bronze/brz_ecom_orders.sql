-- Bronze: e-commerce order lines. union_by_name absorbs additive schema drift
-- (promo_code appears from batch 2026-05); missing columns arrive as NULL.
select
    * exclude (filename),
    regexp_extract(filename, 'batch=([0-9]{4}-[0-9]{2})', 1) as _batch,
    filename                                                 as _source_file
from read_csv('{{ var("landing") }}/ecom/*/*.csv',
              header = true, all_varchar = true, union_by_name = true, filename = true)
