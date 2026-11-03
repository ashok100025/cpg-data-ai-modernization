{{ config(materialized='incremental', incremental_strategy='append') }}
-- Silver: both sales sources conformed to ONE contract (contracts/sales_line.yml), every row
-- kept with a dq_reason. Append-only and incremental by ingestion time, so a new batch only
-- processes new files; history stays replayable from bronze with --full-refresh.

with pos as (
    select
        'POS'                                                     as source_system,
        TXN_ID                                                    as source_txn_id,
        try_cast(LINE_NO as integer)                              as source_line_no,
        'STORE'                                                   as channel,
        nullif(trim(STORE_CODE), '')                              as store_code,
        SKU                                                       as sku,
        case when try_cast(QTY as double) = floor(try_cast(QTY as double))
             then cast(try_cast(QTY as double) as integer) end   as qty_abs,
        case when TXN_TYPE = 'RETURN' then 'RETURN' else 'SALE' end as txn_type,
        try_cast(UNIT_PRICE as decimal(12, 2))                    as unit_price,
        CURRENCY                                                  as currency_code,
        try_strptime(TXN_TS_LOCAL, '%Y-%m-%d %H:%M:%S')           as ts_local,
        cast(null as timestamp)                                   as ts_utc,
        cast(null as varchar)                                     as promo_code,
        try_cast(LOADED_AT as timestamp)                          as ingested_at,
        _batch, _source_file
    from {{ ref('brz_pos_sales') }}
),
ecom as (
    select
        'ECOM', order_id, try_cast(item_seq as integer), 'ECOM',
        x.store_code,
        'SKU-' || replace(product_code, 'P-', ''),
        abs(try_cast(quantity as integer)),
        case when event_type = 'refund' or try_cast(quantity as integer) < 0 then 'RETURN' else 'SALE' end,
        try_cast(price_amount as decimal(12, 2)),
        price_ccy,
        cast(null as timestamp),
        try_strptime(event_time_utc, '%Y-%m-%dT%H:%M:%SZ'),
        nullif(promo_code, ''),
        try_cast(ingested_at as timestamp),
        _batch, _source_file
    from {{ ref('brz_ecom_orders') }} e
    left join {{ ref('fulfilment_node_xref') }} x on e.fulfilment_node = x.fulfilment_node
),
unioned as (
    select * from pos
    union all
    select * from ecom
),
new_rows as (
    select * from unioned
    {% if is_incremental() %}
    where ingested_at > (select max(ingested_at) from {{ this }})
    {% endif %}
),
store_tz as (
    select store_code, max(utc_offset_min) as utc_offset_min, max(currency_code) as store_currency
    from {{ ref('slv_store_history') }} group by 1
),
known_sku as (select distinct sku from {{ ref('slv_product_history') }}),
typed as (
    select
        n.*,
        coalesce(n.ts_utc, n.ts_local - to_minutes(s.utc_offset_min))            as event_ts_utc,
        cast(coalesce(n.ts_local, n.ts_utc + to_minutes(s.utc_offset_min)) as date) as event_date_local,
        cast(strptime(n._batch || '-01', '%Y-%m-%d') as date)                    as batch_period_start,
        s.store_currency,
        k.sku is not null                                                        as sku_known
    from new_rows n
    left join store_tz s on n.store_code = s.store_code
    left join known_sku k on n.sku = k.sku
),
hashed as (
    select *,
        md5(source_system || '|' || source_txn_id || '|' || cast(source_line_no as varchar)) as k,
        md5(concat_ws('|', store_code, sku, txn_type, cast(qty_abs as varchar), cast(unit_price as varchar),
                      currency_code, cast(event_ts_utc as varchar)))                        as row_hash
    from typed
),
flagged as (
    -- An exact retry is a line whose identical content was already received (earlier in this
    -- load or in a previous load). It is collapsed as a duplicate, never judged as "late".
    select h.*,
        (row_number() over (partition by h.k, h.row_hash order by h.ingested_at, h.source_file) > 1
         {% if is_incremental() %}
         or exists (select 1 from {{ this }} t where t.sales_line_key = h.k and t.row_hash = h.row_hash)
         {% endif %}) as is_exact_retry
    from (select *, _source_file as source_file from hashed) h
)
select
    k as sales_line_key, row_hash, is_exact_retry,
    source_system, source_txn_id, source_line_no, channel, store_code, sku, txn_type,
    case when txn_type = 'RETURN' then -qty_abs else qty_abs end as qty,
    unit_price, currency_code, event_ts_utc, event_date_local, promo_code,
    ingested_at, _batch as batch_id, _source_file as source_file,
    greatest(date_diff('day', event_date_local, batch_period_start), 0) as days_late,
    case
        when store_code is null                         then 'MISSING_STORE'
        when not sku_known                              then 'UNKNOWN_SKU'
        when unit_price is null or unit_price < 0       then 'INVALID_PRICE'
        when qty_abs is null or qty_abs = 0             then 'INVALID_QTY'
        when event_ts_utc is null                       then 'INVALID_TIMESTAMP'
        when currency_code <> store_currency            then 'CURRENCY_MISMATCH'
        when not is_exact_retry
         and date_diff('day', event_date_local, batch_period_start) > {{ var('late_window_days') }}
                                                        then 'LATE_BEYOND_WINDOW'
    end as dq_reason
from flagged
