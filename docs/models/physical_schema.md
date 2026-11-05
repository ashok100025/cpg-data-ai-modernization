# Physical schema

> **Generated** by `make schema-doc` from dbt's manifest and catalog – do not edit by hand.
> Section 1 is the production design on Databricks; section 2 is every table and column as built in
> the PoC (DuckDB), with types, descriptions and the tests that guard them.

## 1. Target physical design (Azure Databricks, Unity Catalog)

| Aspect | Design |
|---|---|
| Namespace | `<catalog>.<schema>.<table>` – one catalog per environment: `cpg_dev`, `cpg_test`, `cpg_prod`; schemas `landing` (volumes), `bronze`, `silver`, `gold`, `ref` – same names as the PoC |
| Format | Delta Lake tables, managed by Unity Catalog; landing files in UC **volumes** on ADLS Gen2 |
| Bronze | Auto Loader streaming tables, all source columns kept + `_source_file`, `_batch`, `_ingested_at`; schema evolution `addNewColumns`; rescued-data column for bad types |
| Silver | `slv_sales` as a Delta table updated with `MERGE` on `sales_line_key` (PoC: delete+insert); **change data feed** on, so gold can be incremental |
| Gold | `fct_sales_line` **liquid clustering** on (`event_date_local`, `store_code`, `sku`) – the usual filters; dimensions small, unclustered |
| History | SCD2 dimensions with `valid_from`/`valid_to`/`is_current`; Delta **time travel** kept 30 days for rollback (CI/CD notes) |
| Governance | UC **tags** for sensitivity (`internal`, `commercially_sensitive`) on columns/metric views; row filter on region for regional roles; lineage captured automatically by UC |
| Metrics | Unity Catalog **metric views** generated from `metrics/metrics.yml` (one definition, as in the PoC compiler) |
| Naming | `brz_` / `slv_` / `fct_` / `dim_` / `mart_` prefixes; snake_case; amounts suffixed with currency (`_inr`) |
| Retention | landing 13 months, bronze 25 months, silver/gold indefinite (to confirm – A-13) |

## 2. As built in the PoC (generated)


### Schema `ref`

#### `ref.fulfilment_node_xref`  
*base table (seed, sql)*

E-commerce fulfilment node -> store attribution (assumption A-07).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `fulfilment_node` | VARCHAR |  |  |
| 2 | `store_code` | VARCHAR |  |  |
| 3 | `valid_note` | VARCHAR |  |  |

#### `ref.fx_rates_monthly`  
*base table (seed, sql)*

Monthly average FX rate to INR per currency (assumption A-06). Production - from Treasury / ERP.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `month_start` | DATE |  |  |
| 2 | `currency_code` | VARCHAR |  |  |
| 3 | `rate_to_inr` | DOUBLE |  |  |

#### `ref.region_ref`  
*base table (seed, sql)*

Reference data we own - regions, country, regional-manager role (maps to the access policy).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `region_code` | VARCHAR |  |  |
| 2 | `region_name` | VARCHAR |  |  |
| 3 | `country_code` | VARCHAR |  |  |
| 4 | `region_manager_role` | VARCHAR |  |  |


### Schema `bronze`

#### `bronze.brz_ecom_orders`  
*view (view, sql)*

Bronze - e-commerce lines as landed. union_by_name absorbs additive drift (promo_code from 2026-05; NULL in older batches). Adds _batch and _source_file.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `order_id` | VARCHAR |  |  |
| 2 | `item_seq` | VARCHAR |  |  |
| 3 | `event_time_utc` | VARCHAR |  |  |
| 4 | `fulfilment_node` | VARCHAR |  |  |
| 5 | `product_code` | VARCHAR |  |  |
| 6 | `quantity` | VARCHAR |  |  |
| 7 | `price_amount` | VARCHAR |  |  |
| 8 | `price_ccy` | VARCHAR |  |  |
| 9 | `event_type` | VARCHAR |  |  |
| 10 | `ingested_at` | VARCHAR |  |  |
| 11 | `promo_code` | VARCHAR |  |  |
| 12 | `batch` | VARCHAR |  |  |
| 13 | `_batch` | VARCHAR |  |  |
| 14 | `_source_file` | VARCHAR |  |  |

#### `bronze.brz_erp_material`  
*view (view, sql)*

Bronze - every monthly ERP material extract, kept so product history (SCD2) can be rebuilt at any time.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `material_id` | VARCHAR |  |  |
| 2 | `material_desc` | VARCHAR |  |  |
| 3 | `pack_size` | VARCHAR |  |  |
| 4 | `launch_date` | VARCHAR |  |  |
| 5 | `lifecycle_status` | VARCHAR |  |  |
| 6 | `extract_date` | VARCHAR |  |  |
| 7 | `extract` | DATE |  |  |
| 8 | `_source_file` | VARCHAR |  |  |

#### `bronze.brz_pim_product`  
*view (view, sql)*

Bronze - every monthly PIM product extract (brand, category, marketing pack size).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `sku_code` | VARCHAR |  |  |
| 2 | `brand_name` | VARCHAR |  |  |
| 3 | `category_name` | VARCHAR |  |  |
| 4 | `pack_size` | VARCHAR |  |  |
| 5 | `marketing_name` | VARCHAR |  |  |
| 6 | `extract_date` | VARCHAR |  |  |
| 7 | `extract` | DATE |  |  |
| 8 | `_source_file` | VARCHAR |  |  |

#### `bronze.brz_pos_sales`  
*view (view, sql)*

Bronze - POS lines exactly as landed, every column as text (schema-on-read) so a source type change never breaks loading. Adds _batch (from the folder name) and _source_file for lineage.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `TXN_ID` | VARCHAR |  |  |
| 2 | `LINE_NO` | VARCHAR |  |  |
| 3 | `TXN_TS_LOCAL` | VARCHAR |  |  |
| 4 | `STORE_CODE` | VARCHAR |  |  |
| 5 | `SKU` | VARCHAR |  |  |
| 6 | `QTY` | VARCHAR |  |  |
| 7 | `UNIT_PRICE` | VARCHAR |  |  |
| 8 | `CURRENCY` | VARCHAR |  |  |
| 9 | `TXN_TYPE` | VARCHAR |  |  |
| 10 | `LOADED_AT` | VARCHAR |  |  |
| 11 | `batch` | VARCHAR |  |  |
| 12 | `_batch` | VARCHAR |  |  |
| 13 | `_source_file` | VARCHAR |  |  |

#### `bronze.brz_promotions`  
*view (view, sql)*

Bronze - trade promotion calendar (promotion, SKU, region, dates, discount).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `promo_id` | VARCHAR |  |  |
| 2 | `sku` | VARCHAR |  |  |
| 3 | `region_code` | VARCHAR |  |  |
| 4 | `start_date` | VARCHAR |  |  |
| 5 | `end_date` | VARCHAR |  |  |
| 6 | `discount_pct` | VARCHAR |  |  |
| 7 | `_source_file` | VARCHAR |  |  |

#### `bronze.brz_store_master`  
*view (view, sql)*

Bronze - every monthly store-master extract (store to region, time zone, currency).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `store_code` | VARCHAR |  |  |
| 2 | `store_name` | VARCHAR |  |  |
| 3 | `region_code` | VARCHAR |  |  |
| 4 | `utc_offset_min` | VARCHAR |  |  |
| 5 | `currency` | VARCHAR |  |  |
| 6 | `extract_date` | VARCHAR |  |  |
| 7 | `extract` | DATE |  |  |
| 8 | `_source_file` | VARCHAR |  |  |


### Schema `silver`

#### `silver.slv_dq_batch_summary`  
*base table (table, sql)*

Silver - monitoring signal per batch and source - rows landed, valid, quarantined (by reason), exact retries collapsed, late rows accepted / held, % quarantined. Feeds the anomaly warning test.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `batch_id` | VARCHAR |  |  |
| 2 | `source_system` | VARCHAR |  |  |
| 3 | `rows_landed` | BIGINT |  |  |
| 4 | `rows_valid` | BIGINT |  |  |
| 5 | `rows_quarantined` | BIGINT |  |  |
| 6 | `exact_retries_collapsed` | BIGINT |  |  |
| 7 | `late_rows_accepted` | BIGINT |  |  |
| 8 | `late_rows_held` | BIGINT |  |  |
| 9 | `unknown_sku` | BIGINT |  |  |
| 10 | `invalid_price` | BIGINT |  |  |
| 11 | `missing_store` | BIGINT |  |  |
| 12 | `pct_quarantined` | DOUBLE |  |  |

#### `silver.slv_product_conflicts`  
*base table (table, sql)*

Silver - work queue for Master Data - ERP vs PIM disagreements in the latest extract.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `sku` | VARCHAR |  |  |
| 2 | `extract_date` | DATE |  |  |
| 3 | `erp_pack_size` | VARCHAR |  |  |
| 4 | `pim_pack_size` | VARCHAR |  |  |
| 5 | `conflict_type` | VARCHAR |  |  |

#### `silver.slv_product_history`  
*base table (table, sql)*

Silver - ERP and PIM extracts joined per SKU and extract month with survivorship rules (ERP owns identity, pack size, launch date, status; PIM owns brand and category) and a pack-size conflict flag.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `sku` | VARCHAR |  |  |
| 2 | `extract_date` | DATE |  |  |
| 3 | `product_name` | VARCHAR |  |  |
| 4 | `brand_name` | VARCHAR |  |  |
| 5 | `category_name` | VARCHAR |  |  |
| 6 | `pack_size` | VARCHAR |  |  |
| 7 | `launch_date` | DATE |  |  |
| 8 | `lifecycle_status` | VARCHAR |  |  |
| 9 | `pim_pack_size` | VARCHAR |  |  |
| 10 | `in_erp` | BOOLEAN |  |  |
| 11 | `in_pim` | BOOLEAN |  |  |
| 12 | `has_pack_size_conflict` | BOOLEAN |  |  |

#### `silver.slv_sales`  
*base table (incremental, sql)*

Silver, incremental delete+insert - valid, de-duplicated sales lines; one row per business key (source system + transaction id + line). Retries collapse; the latest correction wins.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `sales_line_key` | VARCHAR | md5(source_system / source_txn_id / source_line_no) | not_null, unique |
| 2 | `row_hash` | VARCHAR |  |  |
| 3 | `is_exact_retry` | BOOLEAN |  |  |
| 4 | `source_system` | VARCHAR |  |  |
| 5 | `source_txn_id` | VARCHAR |  |  |
| 6 | `source_line_no` | INTEGER |  |  |
| 7 | `channel` | VARCHAR |  |  |
| 8 | `store_code` | VARCHAR |  |  |
| 9 | `sku` | VARCHAR |  |  |
| 10 | `txn_type` | VARCHAR |  |  |
| 11 | `qty` | INTEGER |  |  |
| 12 | `unit_price` | DECIMAL(12,2) |  |  |
| 13 | `currency_code` | VARCHAR |  |  |
| 14 | `event_ts_utc` | TIMESTAMP |  |  |
| 15 | `event_date_local` | DATE |  |  |
| 16 | `promo_code` | VARCHAR |  |  |
| 17 | `ingested_at` | TIMESTAMP |  |  |
| 18 | `batch_id` | VARCHAR |  |  |
| 19 | `source_file` | VARCHAR |  |  |
| 20 | `days_late` | BIGINT |  |  |
| 21 | `versions_in_load` | BIGINT |  |  |
| 22 | `is_late_arrival` | BOOLEAN |  |  |

#### `silver.slv_sales_conformed`  
*base table (incremental, sql)*

Silver, incremental append - both sales sources conformed to one contract (UTC + local date, signed quantity, SKU-codes), one row per landed line with dq_reason (NULL = valid), is_exact_retry and days_late. Processes only rows ingested after the last run.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `sales_line_key` | VARCHAR |  |  |
| 2 | `row_hash` | VARCHAR |  |  |
| 3 | `is_exact_retry` | BOOLEAN |  |  |
| 4 | `source_system` | VARCHAR |  |  |
| 5 | `source_txn_id` | VARCHAR |  |  |
| 6 | `source_line_no` | INTEGER |  |  |
| 7 | `channel` | VARCHAR |  |  |
| 8 | `store_code` | VARCHAR |  |  |
| 9 | `sku` | VARCHAR |  |  |
| 10 | `txn_type` | VARCHAR |  |  |
| 11 | `qty` | INTEGER |  |  |
| 12 | `unit_price` | DECIMAL(12,2) |  |  |
| 13 | `currency_code` | VARCHAR |  |  |
| 14 | `event_ts_utc` | TIMESTAMP |  |  |
| 15 | `event_date_local` | DATE |  |  |
| 16 | `promo_code` | VARCHAR |  |  |
| 17 | `ingested_at` | TIMESTAMP |  |  |
| 18 | `batch_id` | VARCHAR |  |  |
| 19 | `source_file` | VARCHAR |  |  |
| 20 | `days_late` | BIGINT |  |  |
| 21 | `dq_reason` | VARCHAR |  |  |

#### `silver.slv_sales_quarantine`  
*base table (table, sql)*

Silver - rows that failed a quality rule, with the reason. Never silently dropped; LATE_BEYOND_WINDOW rows go to Finance's restatement process.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `sales_line_key` | VARCHAR |  |  |
| 2 | `row_hash` | VARCHAR |  |  |
| 3 | `is_exact_retry` | BOOLEAN |  |  |
| 4 | `source_system` | VARCHAR |  |  |
| 5 | `source_txn_id` | VARCHAR |  |  |
| 6 | `source_line_no` | INTEGER |  |  |
| 7 | `channel` | VARCHAR |  |  |
| 8 | `store_code` | VARCHAR |  |  |
| 9 | `sku` | VARCHAR |  |  |
| 10 | `txn_type` | VARCHAR |  |  |
| 11 | `qty` | INTEGER |  |  |
| 12 | `unit_price` | DECIMAL(12,2) |  |  |
| 13 | `currency_code` | VARCHAR |  |  |
| 14 | `event_ts_utc` | TIMESTAMP |  |  |
| 15 | `event_date_local` | DATE |  |  |
| 16 | `promo_code` | VARCHAR |  |  |
| 17 | `ingested_at` | TIMESTAMP |  |  |
| 18 | `batch_id` | VARCHAR |  |  |
| 19 | `source_file` | VARCHAR |  |  |
| 20 | `days_late` | BIGINT |  |  |
| 21 | `dq_reason` | VARCHAR | Quality rule that failed. | accepted_values, not_null |

#### `silver.slv_store_history`  
*base table (table, sql)*

Silver - typed store reference, one row per store per monthly extract. Input to dim_store (SCD2).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `store_code` | VARCHAR |  |  |
| 2 | `store_name` | VARCHAR |  |  |
| 3 | `region_code` | VARCHAR |  |  |
| 4 | `utc_offset_min` | INTEGER |  |  |
| 5 | `currency_code` | VARCHAR |  |  |
| 6 | `extract_date` | DATE |  |  |


### Schema `gold`

#### `gold.dim_date`  
*base table (table, sql)*

Gold - calendar 2024-2027 with the fiscal calendar (year from the Monday of the week containing 1 April; 13-week quarters split 4-4-5).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `date_key` | INTEGER |  | not_null, unique |
| 2 | `date_day` | DATE |  |  |
| 3 | `week_start` | DATE |  |  |
| 4 | `iso_day_of_week` | BIGINT |  |  |
| 5 | `day_name` | VARCHAR |  |  |
| 6 | `month_start` | DATE |  |  |
| 7 | `calendar_year` | BIGINT |  |  |
| 8 | `fiscal_year` | VARCHAR |  |  |
| 9 | `fiscal_quarter` | BIGINT |  |  |
| 10 | `fiscal_week` | BIGINT |  |  |
| 11 | `fiscal_period` | BIGINT |  |  |

#### `gold.dim_product`  
*base table (table, sql)*

Gold - product dimension, SCD type 2. New version only when brand, category, pack size or lifecycle status changes; valid_from / valid_to from extract dates. One current row per SKU.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `product_sk` | VARCHAR |  | not_null, unique |
| 2 | `sku` | VARCHAR |  | not_null |
| 3 | `product_name` | VARCHAR |  |  |
| 4 | `brand_name` | VARCHAR |  |  |
| 5 | `category_name` | VARCHAR |  |  |
| 6 | `pack_size` | VARCHAR |  |  |
| 7 | `launch_date` | DATE |  |  |
| 8 | `lifecycle_status` | VARCHAR |  |  |
| 9 | `version_no` | BIGINT |  |  |
| 10 | `valid_from` | DATE |  |  |
| 11 | `valid_to` | DATE |  |  |
| 12 | `is_current` | BOOLEAN |  |  |

#### `gold.dim_region`  
*base table (table, sql)*

Gold - regions with country and the regional-manager role used by the access policy.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `region_code` | VARCHAR |  | not_null, unique |
| 2 | `region_name` | VARCHAR |  |  |
| 3 | `country_code` | VARCHAR |  |  |
| 4 | `region_manager_role` | VARCHAR |  |  |

#### `gold.dim_store`  
*base table (table, sql)*

Gold - store dimension, SCD type 2 incl. region. Facts join the version valid on the sale date (as-was); is_current gives as-is.

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `store_sk` | VARCHAR |  | not_null, unique |
| 2 | `store_code` | VARCHAR |  |  |
| 3 | `store_name` | VARCHAR |  |  |
| 4 | `region_code` | VARCHAR |  | not_null, relationships |
| 5 | `currency_code` | VARCHAR |  |  |
| 6 | `utc_offset_min` | INTEGER |  |  |
| 7 | `version_no` | BIGINT |  |  |
| 8 | `valid_from` | DATE |  |  |
| 9 | `valid_to` | DATE |  |  |
| 10 | `is_current` | BOOLEAN |  |  |

#### `gold.fct_sales_line`  
*base table (table, sql)* · **contract enforced**

Sales fact at the grain of one source sales/return line event. Signed quantities; amounts in INR. Contract-enforced: a change to names or types fails the build (see docs/delivery/cicd.md).

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `sales_line_key` | VARCHAR | md5(source_system / source_txn_id / source_line_no) - the business key | not_null, unique |
| 2 | `date_key` | INTEGER | Sale date as yyyymmdd (local date of the store). | not_null, relationships |
| 3 | `event_date_local` | DATE | Sale date in the store's local time zone. | not_null |
| 4 | `event_ts_utc` | TIMESTAMP | Sale timestamp in UTC. |  |
| 5 | `store_sk` | VARCHAR | Store version valid on the sale date (as-was) - dim_store. | not_null, relationships |
| 6 | `store_code` | VARCHAR | Store business key; online orders use the fulfilling store (A-07). |  |
| 7 | `region_code_at_sale` | VARCHAR | region the store belonged to on the sale date (as-was) |  |
| 8 | `product_sk` | VARCHAR | Product version valid on the sale date (as-was) - dim_product. | not_null, relationships |
| 9 | `sku` | VARCHAR | Product business key (SKU-nnnn). |  |
| 10 | `source_system` | VARCHAR | Reporting system - POS or ECOM. | accepted_values |
| 11 | `source_txn_id` | VARCHAR | Transaction / order id in the source system. |  |
| 12 | `source_line_no` | INTEGER | Line number within the source transaction. |  |
| 13 | `channel` | VARCHAR | STORE or ECOM. | accepted_values |
| 14 | `txn_type` | VARCHAR | SALE or RETURN. | accepted_values |
| 15 | `qty` | INTEGER | Signed quantity - returns negative. | not_null |
| 16 | `units_sold` | INTEGER | max(qty, 0). |  |
| 17 | `units_returned` | INTEGER | max(-qty, 0). |  |
| 18 | `unit_price_local` | DECIMAL(12,2) | Price paid per unit in local currency (after promotion discount). |  |
| 19 | `currency_code` | VARCHAR | ISO currency of the sale (INR, AED). |  |
| 20 | `fx_rate_to_inr` | DOUBLE | Monthly average rate to INR (A-06). | not_null |
| 21 | `gross_sales_inr` | DECIMAL(14,2) | Sales value in INR for SALE lines, 0 for returns. Tax excluded (A-01). |  |
| 22 | `returns_inr` | DECIMAL(14,2) | Returned value in INR (positive) for RETURN lines. |  |
| 23 | `net_sales_inr` | DECIMAL(14,2) | Signed value in INR = gross - returns at line level. |  |
| 24 | `promo_id` | VARCHAR | Promotion applied (source promo code or matched promotion calendar). |  |
| 25 | `on_promotion` | BOOLEAN | True when a promotion applied. |  |
| 26 | `is_late_arrival` | BOOLEAN | Line arrived after its batch period started (within the accepted window). |  |
| 27 | `ingested_at` | TIMESTAMP | When the line was loaded - lineage and incremental processing. |  |
| 28 | `batch_id` | VARCHAR | Landing batch (YYYY-MM) the line came from. |  |

#### `gold.mart_sales_weekly`  
*base table (table, python)*

Weekly sales by region (as-was), category (as-was) and channel. Every column is produced by the metric compiler from metrics/metrics.yml. Grain: week x region x category x channel.

Table tests: unique_mart_grain

| # | Column | Type | Description | Tests |
|---|---|---|---|---|
| 1 | `week` | DATE |  | not_null |
| 2 | `region` | VARCHAR |  | not_null |
| 3 | `category` | VARCHAR |  | not_null |
| 4 | `channel` | VARCHAR |  | not_null |
| 5 | `gross_sales` | DECIMAL(38,2) |  |  |
| 6 | `returns_value` | DECIMAL(38,2) |  |  |
| 7 | `net_revenue` | DECIMAL(38,2) |  |  |
| 8 | `units_sold` | HUGEINT |  |  |
| 9 | `units_returned` | HUGEINT |  |  |
| 10 | `net_units` | HUGEINT |  |  |
| 11 | `promo_revenue` | DECIMAL(38,2) |  |  |
| 12 | `return_rate` | DOUBLE |  |  |
| 13 | `avg_selling_price` | DOUBLE |  |  |
| 14 | `promo_revenue_share` | DOUBLE |  |  |


### Sources (landing files)

| Source | Owner | Location | Description |
|---|---|---|---|
| `landing.ecom` | Digital Commerce | `read_csv('data/raw/landing/ecom/*/*.csv')` | E-commerce order and refund lines (schema B, UTC, refunds as -qty, P- product codes; promo_code added from 2026-05). Monthly batches. |
| `landing.erp_product` | Master Data (ERP) | `read_csv('data/raw/landing/erp_product/*/*.csv')` | ERP material master, monthly full extract. Owns identity, pack size, launch date, lifecycle status. |
| `landing.pim_product` | Marketing (PIM) | `read_csv('data/raw/landing/pim_product/*/*.csv')` | PIM product master, monthly full extract. Owns brand and category. |
| `landing.pos` | Retail IT (POS platform) | `read_csv('data/raw/landing/pos/*/*.csv')` | Store POS sales and return lines (schema A, local time, returns as +qty with TXN_TYPE=RETURN). Monthly batches `batch=YYYY-MM`. |
| `landing.promotions` | Trade Marketing | `read_csv('data/raw/landing/promotions/*.csv')` | Trade promotion calendar (single file). |
| `landing.store_ref` | Sales Operations | `read_csv('data/raw/landing/store_ref/*/*.csv')` | Store master, monthly full extract. Owns store name, region, time zone, currency. |
