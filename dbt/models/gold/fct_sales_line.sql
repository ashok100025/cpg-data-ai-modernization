-- Gold: sales fact. Grain = one source sales or return line event (business key = source
-- system + transaction id + line number). Quantities are signed (returns negative).
-- Amounts are converted to the reporting currency at the monthly average rate (assumption A-06).
-- accounting_month = the month the line counts in Finance's books (= sale month unless Finance booked a
-- restatement in a later month, ADR-004); restated lines carry their restatement_id.
-- Dimensions are joined as-was: the product/store version valid on the local sale date.
with promo as (
    select sku, region_code, cast(start_date as date) as start_date, cast(end_date as date) as end_date,
           promo_id, cast(discount_pct as integer) as discount_pct
    from {{ ref('brz_promotions') }}
),
base as (
    select s.*, st.store_sk, st.region_code as region_code_at_sale, p.product_sk, fx.rate_to_inr
    from {{ ref('slv_sales') }} s
    left join {{ ref('dim_store') }} st
           on s.store_code = st.store_code and s.event_date_local between st.valid_from and st.valid_to
    left join {{ ref('dim_product') }} p
           on s.sku = p.sku and s.event_date_local between p.valid_from and p.valid_to
    left join {{ ref('fx_rates_monthly') }} fx
           on cast(date_trunc('month', s.event_date_local) as date) = fx.month_start
          and s.currency_code = fx.currency_code
),
with_promo as (
    select b.*, pr.promo_id as matched_promo_id
    from base b
    left join promo pr
           on b.sku = pr.sku and b.region_code_at_sale = pr.region_code
          and b.event_date_local between pr.start_date and pr.end_date
    qualify row_number() over (partition by b.sales_line_key order by pr.start_date desc nulls last) = 1
)
select
    cast(sales_line_key as varchar)                                         as sales_line_key,
    cast(strftime(event_date_local, '%Y%m%d') as integer)                   as date_key,
    cast(event_date_local as date)                                          as event_date_local,
    cast(event_ts_utc as timestamp)                                         as event_ts_utc,
    cast(store_sk as varchar)                                               as store_sk,
    cast(store_code as varchar)                                             as store_code,
    cast(region_code_at_sale as varchar)                                    as region_code_at_sale,
    cast(product_sk as varchar)                                             as product_sk,
    cast(sku as varchar)                                                    as sku,
    cast(source_system as varchar)                                          as source_system,
    cast(source_txn_id as varchar)                                          as source_txn_id,
    cast(source_line_no as integer)                                         as source_line_no,
    cast(channel as varchar)                                                as channel,
    cast(txn_type as varchar)                                               as txn_type,
    cast(qty as integer)                                                    as qty,
    cast(greatest(qty, 0) as integer)                                       as units_sold,
    cast(greatest(-qty, 0) as integer)                                      as units_returned,
    cast(unit_price as decimal(12, 2))                                      as unit_price_local,
    cast(currency_code as varchar)                                          as currency_code,
    cast(rate_to_inr as double)                                             as fx_rate_to_inr,
    cast(round(greatest(qty, 0) * unit_price * rate_to_inr, 2) as decimal(14, 2))  as gross_sales_inr,
    cast(round(greatest(-qty, 0) * unit_price * rate_to_inr, 2) as decimal(14, 2)) as returns_inr,
    cast(round(qty * unit_price * rate_to_inr, 2) as decimal(14, 2))        as net_sales_inr,
    cast(coalesce(promo_code, matched_promo_id) as varchar)                 as promo_id,
    coalesce(promo_code, matched_promo_id) is not null                      as on_promotion,
    cast(is_late_arrival as boolean)                                        as is_late_arrival,
    cast(accounting_month as varchar)                                       as accounting_month,
    cast(restatement_id as varchar)                                         as restatement_id,
    cast(is_restated as boolean)                                            as is_restated,
    cast(ingested_at as timestamp)                                          as ingested_at,
    cast(batch_id as varchar)                                               as batch_id
from with_promo
