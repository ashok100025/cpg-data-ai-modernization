-- Every natural key has exactly one current version and no overlapping validity windows.
with v as (
    select 'product' as dim, sku as nk, valid_from, valid_to, is_current from {{ ref('dim_product') }}
    union all
    select 'store', store_code, valid_from, valid_to, is_current from {{ ref('dim_store') }}
),
overlapping as (
    select a.dim, a.nk from v a join v b
      on a.dim = b.dim and a.nk = b.nk and a.valid_from < b.valid_from and a.valid_to >= b.valid_from
),
currents as (
    select dim, nk from v group by 1, 2 having count(*) filter (where is_current) <> 1
)
select * from overlapping union all select * from currents
