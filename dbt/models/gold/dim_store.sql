-- Gold: store dimension, SCD type 2 on region and store attributes. Facts join on the
-- version valid at the sale date (as-was); "as-is" reporting uses is_current (ADR-002).
with h as (
    select *, md5(concat_ws('|', store_name, region_code, currency_code, cast(utc_offset_min as varchar))) as attr_hash
    from {{ ref('slv_store_history') }}
),
chg as (select *, lag(attr_hash) over (partition by store_code order by extract_date) as prev_hash from h),
versions as (
    select *,
        row_number() over (partition by store_code order by extract_date) as version_no,
        lead(extract_date) over (partition by store_code order by extract_date) as next_from
    from chg where prev_hash is null or prev_hash <> attr_hash
)
select
    md5(store_code || '|' || cast(extract_date as varchar))                as store_sk,
    store_code, store_name, region_code, currency_code, utc_offset_min, version_no,
    case when version_no = 1 then date '1900-01-01' else extract_date end  as valid_from,
    coalesce(next_from - 1, date '9999-12-31')                             as valid_to,
    next_from is null                                                      as is_current
from versions
