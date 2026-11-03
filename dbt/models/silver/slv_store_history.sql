-- Typed store reference, one row per store per monthly extract.
select
    store_code,
    store_name,
    region_code,
    cast(utc_offset_min as integer) as utc_offset_min,
    currency                        as currency_code,
    cast(extract_date as date)      as extract_date
from {{ ref('brz_store_master') }}
