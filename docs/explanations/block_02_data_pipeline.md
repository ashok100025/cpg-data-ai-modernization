# Block 2 – Synthetic data → bronze → silver → gold

**Status:** built and verified locally on 2026-11-04 (02:10–02:20 IST); reviewed and accepted by Ashok
(02:47 IST); pushed to GitHub on approval (02:55 IST).

**In one line:** create realistic messy sales data, then build the pipeline that cleans it, keeps
history, catches bad data, and produces one trusted sales table that everything else uses.

---

## Why this block (PDF links)

| PDF says | Where |
|---|---|
| *"A representative data flow ingests sample sales and reference data, applies quality rules, preserves history where relevant, and exposes a queryable curated model."* | Page 2, functional requirement #2 – **this block is exactly this** |
| *"Design ingestion, validation, transformation, and serving layers. Address batch and incremental loads, schema drift, late data, deduplication, lineage, and failure recovery."* | Page 1, problem area 2 |
| *"Define business entities, measures, grain, keys, history, and data contracts… physical schema for sales, product, location."* | Page 1, problem area 1 |
| *"Sources differ in schema and identifiers; retries, corrections, and late arrivals occur… Product attributes change over time and may have conflicting source ownership… A store can be reassigned between regions."* | Page 1, Data Landscape |
| *"Working proof-of-concept source, sample or synthetic data, automated tests… reproducible outputs."* | Page 3, Deliverable 1 |
| *"Working demo… show a quality failure"* | Page 3, Video |

Metrics, forecast and AI all read this block's output: if this data is wrong, everything is wrong.

## How – five steps

### Step 1 – Synthetic data generator (`src/poc/generate_data.py`)
No client data exists, so a script **creates** it with a fixed seed – every run gives identical files.

Company: 12 stores (10 India, 2 UAE), 40 products in 4 categories, Jan 2025 – Sep 2026, ~220k sales lines.

| Source | What makes it realistic |
|---|---|
| Store POS sales | Local time; returns as **positive** qty with type RETURN; ids `SKU-0001` |
| E-commerce orders | **UTC** time; refunds as **negative** qty; ids `P-0001`; new column from May 2026 |
| ERP product master | Owns pack size, status, launch date |
| PIM product master | Owns brand, category; **disagrees with ERP** on one product |
| Store master | Store → region; **S003 moves SOUTH → WEST on 1 Jul 2026** |
| Promotions | Discounts by product and region; lift sales |

| Fault injected | PDF phrase |
|---|---|
| Same sale sent twice | "retries" |
| Same sale re-sent with corrected qty | "corrections" |
| A store's data arrives weeks later | "late arrivals" |
| New column; qty sent as `"3.0"` | "schema drift" |
| Unknown product, negative price, missing store | "applies quality rules" |
| Product changes category; store changes region | "attributes change over time"; "store can be reassigned" |
| ERP and PIM disagree | "conflicting source ownership" |

### Step 2 – Bronze (raw, as received)
Read landed files **as text**, untouched, plus source file and batch per row.
- Text-first → a source sending `"3.0"` or a new column never crashes loading (**schema drift**, **failure recovery**: raw is kept, anything can be rebuilt).
- Source file per row → **lineage**.

### Step 3 – Silver (cleaned and checked)
1. **Conform** both sales sources to one format (UTC + local time, returns negative, `P-0001` → `SKU-0001`).
2. **Quality rules** – failures go to a **quarantine table with a reason**; never silently deleted.
3. **De-duplicate** on the **business key** (source + transaction id + line no): retries collapse, latest correction wins.
4. **Late data** – accepted up to 14 days; older is held for Finance rather than changing a closed month.
5. **Incremental** – a new batch processes only new files.
6. **Monitoring table** – per batch: landed, passed, held, and why.

### Step 4 – Gold (business-ready "curated model")
- `fct_sales_line` – **grain: one sale or return line**; INR amounts; linked to product, store, date; protected by a **data contract** (build fails if a column changes).
- `dim_product`, `dim_store` – **SCD2** history with valid-from / valid-to.
- **As-was** attribution by default (June sale of S003 stays SOUTH); as-is also available.
- `dim_date` – includes the 4-4-5 fiscal calendar.

### Step 5 – Automated tests and run path
- ~50 dbt data tests: unique keys, no orphans, SCD2 without overlaps, gold reconciles to silver, S003 region rule.
- YAML data contracts in `contracts/` – what each source promises, owner, change policy.
- `Makefile`: `make setup`, `make all`, `make demo-incremental` (October batch with late and bad rows – for the video).

---

# Exact inventory – what Block 2 creates

## A. Files in the repo (committed)

| # | File | What it is |
|---|---|---|
| 1 | `src/poc/generate_data.py` | Python script that creates the synthetic data (fixed seed) |
| 2 | `src/poc/__init__.py` | Empty marker so `src/poc` is a Python package |
| 3 | `dbt/dbt_project.yml` | dbt project config – layers, schemas, variables (14-day late window, INR) |
| 4 | `dbt/profiles.yml` | Connection – points dbt at the local DuckDB file |
| 5 | `dbt/macros/generate_schema_name.sql` | Makes tables land in schemas named `bronze`, `silver`, `gold`, `ref` |
| 6 | `dbt/seeds/*.csv` (3) | Small reference tables we maintain (section C) |
| 7 | `dbt/models/bronze/*.sql` (6) | Bronze models (section D) |
| 8 | `dbt/models/silver/*.sql` (7) + `_silver.yml` | Silver models and their tests |
| 9 | `dbt/models/gold/*.sql` (5) + `_gold.yml` | Gold models, tests, and the fact's enforced contract |
| 10 | `dbt/tests/*.sql` (4) | Custom business tests (section G) |
| 11 | `contracts/source_contracts.yml` | Inbound contracts for the 5 sources – columns, owner, key, late-data rule, change policy |
| 12 | `contracts/fct_sales_line.yml` | Outbound contract for the sales fact – grain, key, semantics, consumers, versioning |
| 13 | `Makefile` | Commands: `setup`, `data`, `build`, `demo-incremental`, `inspect`, `preview`, `query`, `all`, `clean` |
| 13a | `src/poc/inspect_warehouse.py` | *Added after review:* `make inspect` (every schema/table with row counts, reconciliation, quarantine by reason), `make preview TABLE=…` (first rows of a table), `make query SQL="…"` (any read-only SQL) |
| 14 | `README.md` (update) | "Run it" section + table: each fault → how handled → where to see it + *"Explore the results"* (added after review) |
| 15 | `methodology/*.csv` (update) | Block 2 rows in time log, decision log, coaching moments |
| 16 | this file (update) | Status → built, plus verification results |

## B. Generated data (on disk, not committed – recreated by `make data`)

`data/raw/landing/` – 106 CSV files:

| Folder | Files | One row = |
|---|---|---|
| `pos/batch=2025-01 … 2026-09/pos_sales.csv` | 21 | one POS sale/return line |
| `ecom/batch=…/ecom_orders.csv` | 21 | one e-commerce order/refund line |
| `erp_product/extract=YYYY-MM-01/erp_material.csv` | 21 | one product in that month's ERP extract |
| `pim_product/extract=…/pim_product.csv` | 21 | one product in that month's PIM extract |
| `store_ref/extract=…/store_master.csv` | 21 | one store in that month's extract |
| `promotions/promotions.csv` | 1 | one promotion |

`make demo-incremental` adds 5 files for October 2026.
Database: `data/warehouse/cpg.duckdb` with 4 schemas – **ref, bronze, silver, gold**.

## C. Seeds (schema `ref`) – 3 tables

| Table | Rows | Purpose |
|---|---|---|
| `region_ref` | 5 | Region code, name, country, region-manager role (used later for access control) |
| `fulfilment_node_xref` | 4 | E-commerce fulfilment node (FN-01…) → store (S001…) |
| `fx_rates_monthly` | 48 | Monthly INR and AED → INR rates |

## D. Bronze (schema `bronze`) – 6 views over the files

All columns as text, plus `_source_file` and `_batch`.

| View | Reads |
|---|---|
| `brz_pos_sales` | all POS batch files |
| `brz_ecom_orders` | all e-commerce files (absorbs the new `promo_code` column) |
| `brz_erp_material` | all ERP extracts |
| `brz_pim_product` | all PIM extracts |
| `brz_store_master` | all store extracts |
| `brz_promotions` | promotions file |

## E. Silver (schema `silver`) – 7 tables

| Table | Type | Grain (one row =) | Purpose |
|---|---|---|---|
| `slv_store_history` | table | store × extract month | Typed store reference |
| `slv_product_history` | table | product × extract month | ERP + PIM merged with survivorship rules + conflict flag |
| `slv_product_conflicts` | table | product with a conflict | ERP-vs-PIM work queue for Master Data |
| `slv_sales_conformed` | incremental, append | every landed sales row | Both sources in one format, with `dq_reason` (null = good) and `is_exact_retry` |
| `slv_sales` | incremental, delete+insert | one valid sales line (unique business key) | De-duplicated; latest correction wins |
| `slv_sales_quarantine` | table | one failed row | Rows with `dq_reason`: MISSING_STORE, UNKNOWN_SKU, INVALID_PRICE, INVALID_QTY, INVALID_TIMESTAMP, CURRENCY_MISMATCH, LATE_BEYOND_WINDOW |
| `slv_dq_batch_summary` | table | batch × source | Monitoring: landed / valid / quarantined / retries / late accepted / late held / % quarantined |

## F. Gold (schema `gold`) – 5 tables, the curated model

| Table | Grain | Key | Main columns |
|---|---|---|---|
| `fct_sales_line` | one sale or return line | `sales_line_key` | date_key, event_date_local, event_ts_utc, store_sk, store_code, region_code_at_sale, product_sk, sku, source_system, channel, txn_type, qty (signed), units_sold, units_returned, unit_price_local, currency_code, fx_rate_to_inr, **gross_sales_inr, returns_inr, net_sales_inr**, promo_id, on_promotion, is_late_arrival, ingested_at, batch_id – 28 columns, **contract-enforced** |
| `dim_product` | product version (SCD2) | `product_sk` | sku, name, brand, category, pack_size, launch_date, lifecycle_status, version_no, valid_from, valid_to, is_current |
| `dim_store` | store version (SCD2) | `store_sk` | store_code, name, region_code, currency, utc_offset, version_no, valid_from, valid_to, is_current |
| `dim_region` | region | `region_code` | name, country, manager role |
| `dim_date` | day (2024–2027) | `date_key` | date, week_start, month, fiscal_year, fiscal_quarter, fiscal_week, fiscal_period (4-4-5) |

Expected history: 3 products get 2 versions (pack size change, category reclassification, discontinued);
S003 gets 2 versions (SOUTH → WEST).

## G. Tests – ~52 checks run by `dbt build`

**Generic (in YAML):** unique and not-null on every key; fact links to date/store/product must exist;
allowed values for channel, txn_type, source_system, dq_reason.

**Custom business tests:**

| Test | Checks |
|---|---|
| `assert_scd2_no_overlap_and_one_current` | No overlapping history; exactly one current row per product/store |
| `assert_fact_reconciles_to_silver` | Gold has the same rows and units as validated silver (joins didn't duplicate) |
| `assert_store_reassignment_is_as_was` | S003 is SOUTH before 1 Jul 2026 and WEST from then |
| `assert_quarantine_rate_below_threshold` | **Warning** when a batch quarantines > 3× its trailing 6-batch average and ≥ 0.2% (fires in the October demo) – *changed during build, see below* |

## Totals

21 dbt models (6 bronze, 7 silver, 5 gold, 3 seeds) · ~52 tests · 2 contract files · 1 generator ·
1 Makefile · ~220k sales lines · builds in under 10 seconds.

---

> **Updated in Block 4:** bronze models now read the landing files through dbt **sources**
> (`dbt/models/bronze/_sources.yml`) instead of hard-coded `read_csv` paths, and every model has a
> description – see `block_04_ai_docker_ci.md`. Results are identical.

## Verification results (02:20 IST)

| Check | Expected | Result |
|---|---|---|
| Objects built | 3 ref, 6 bronze, 7 silver, 5 gold | ✅ 3 / 6 / 7 / 5 |
| History build (`make all`) | all tests pass, no warning | ✅ 52 pass, 0 warn |
| October demo (`make demo-incremental`) | only new files processed; 1 monitoring warning | ✅ 51 pass, **1 warn** (POS Oct: 0.40% vs 0.05% baseline) |
| Incremental = full rebuild | identical | ✅ 231,122 rows · 263,398 units · ₹34,250,772.27 · same content hash |
| Landed history never rewritten | 0 changed files | ✅ 0 changed, 5 new |
| Totals after October | – | 232,050 landed → 231,863 passed → **187 held** · 672 retries collapsed · 469 late rows accepted · 99 late rows held |
| Quarantine by reason | all fault types caught | LATE_BEYOND_WINDOW 99 (ECOM 70 corrections + POS 29 offline-store lines) · UNKNOWN_SKU 44 · INVALID_PRICE 22 · MISSING_STORE 22 |
| SCD2 | 3 products + S003 with 2 versions | ✅ SKU-0012 pack 90g→120g (Aug-25) · SKU-0017 Snacks→Healthy Snacks (Apr-26) · SKU-0027 → DISCONTINUED (Mar-26) · S003 SOUTH→WEST (Jul-26) |
| As-was region | S003 SOUTH before 1 Jul, WEST after | ✅ 10,262 lines SOUTH (to 30 Jun) · 2,326 lines WEST (from 1 Jul) |
| ERP vs PIM conflict surfaced | SKU-0002 | ✅ ERP 600ml vs PIM 500 ml → PACK_SIZE_MISMATCH |
| Net sales by region (₹ mn) | – | SOUTH 11.32 · WEST 7.91 · NORTH 7.05 · UAE 4.82 · EAST 3.14 · returns ≈ 2% |

## Changes made during the build (AI output corrected)

| What | Why |
|---|---|
| Quarantine warning: fixed 1% → **anomaly rule** (3× trailing average, ≥ 0.2%) | The promised warning did not fire on the October incident (0.40% < 1%). Thresholds must come from observed baselines and be proven on a bad case (coaching moment C5, decision D8) |
| Removed `dbt/.user.yml` from the repo and ignored it | dbt-generated file with a machine user id; the AI had committed it in the first attempt |
| Removed unused `snapshot-paths` from dbt config | History is built from retained extracts, not dbt snapshots (decision D6) |
| Bronze views no longer carry the file name twice (`filename` + `_source_file`) | Spotted while previewing a bronze view during review; results re-verified identical (same rows, units, revenue, content hash) |

Earlier corrections from the first attempt are kept in the code: retries detected before the late-data
rule (C3) and append-only landing verified by file hashes (C4).

## How dbt is used

**dbt (data build tool)** builds the whole database – from raw files to gold tables. Python does only
two side jobs.

### Who does what

| Job | Done by |
|---|---|
| Create the synthetic source data (106 CSV files) | **Python** – `generate_data.py` |
| Load the 3 small reference CSVs into `ref` | **dbt** – seeds |
| Create 6 bronze views, 7 silver tables, 5 gold tables | **dbt** – models |
| Decide the build order | **dbt** – dependency graph (DAG) |
| Run the 52 quality tests | **dbt** – tests |
| Block the build if the fact's columns change | **dbt** – contract |
| Print the summary | **Python** – `inspect_warehouse.py` (only reads what dbt built) |

### The pieces

1. **Project and connection** – `dbt_project.yml` says where models live and which layer gets which
   schema (bronze = views, silver/gold = tables). `profiles.yml` says *build into
   `data/warehouse/cpg.duckdb`* – the only line tying us to DuckDB.
2. **Models = one SQL `SELECT` per table.** We never write `CREATE TABLE`, `INSERT` or `MERGE`; dbt
   generates them from the model's **materialization**:
   - `view` – bronze
   - `table` – most of silver and gold
   - `incremental` – `slv_sales_conformed` (append new rows only) and `slv_sales` (delete + insert
     changed keys – how corrections replace old versions)
3. **`ref()` = dependencies.** Models refer to each other as `{{ ref('slv_sales') }}`, not by table name.
   dbt derives the **build order** automatically (seeds → bronze → silver → gold); the same graph is the
   **lineage**.
4. **Seeds** – `region_ref.csv`, `fx_rates_monthly.csv`, `fulfilment_node_xref.csv` loaded as tables.
5. **Tests** – *generic* tests are one line in YAML (`unique`, `not_null`, `relationships`,
   `accepted_values`); *custom* tests are SQL queries returning bad rows (0 rows = pass). When a test
   fails, dbt **skips everything downstream** instead of building on bad data (seen in the first attempt:
   the fact and its 16 tests were skipped).
6. **Contract** – `contract: enforced: true` on `fct_sales_line`: if the SQL produces a column name or
   type different from the YAML, the build fails. The data contract made executable.
7. **Variables and macro** – `late_window_days: 14` is a dbt variable used by the late-data rule
   (change in one place); the macro names schemas `bronze` / `silver` / `gold`.

### What the Make commands run

```
make all               = python generate_data.py  →  dbt build --full-refresh
make demo-incremental  = python generate_data.py --demo-batch  →  dbt build   (incremental: only October rows)
```

### Why dbt – the architect's view

- **Portability** – in production the same models run on **Databricks** via the `dbt-databricks` adapter;
  mainly `profiles.yml` changes, plus small SQL dialect tweaks. This answers the PDF's *"explain
  portability, lock-in"* (README stack table, line 50).
- **Answers PDF items directly** – transformation layers (models), quality rules (tests), data contracts
  (contract), lineage (`ref` graph), CI gates (a failing `dbt build` stops the pipeline).

## Where it is built and how to look at it

The pipeline is **real, not conceptual**. Everything is created inside the project folder:

| What | Location |
|---|---|
| Database (all 4 schemas, 21 tables/views) | `data/warehouse/cpg.duckdb` – one file, ~70 MB |
| Raw landed data | `data/raw/landing/` – 111 CSV files (106 history + 5 October demo) |

DuckDB has **no server**: the whole database lives in that one file (like SQLite, but built for analytics).
Both locations are generated and git-ignored – anyone recreates them with `make all`.

### Objects in the database (row counts after the October demo)

| Schema | Object | Type | Rows |
|---|---|---|---|
| ref | fulfilment_node_xref / fx_rates_monthly / region_ref | table | 4 / 48 / 5 |
| bronze | brz_pos_sales | view | 168,985 |
| bronze | brz_ecom_orders | view | 63,065 |
| bronze | brz_erp_material / brz_pim_product | view | 848 / 848 |
| bronze | brz_store_master / brz_promotions | view | 264 / 72 |
| silver | slv_sales_conformed | table | 232,050 |
| silver | slv_sales | table | 231,122 |
| silver | slv_sales_quarantine | table | 187 |
| silver | slv_dq_batch_summary | table | 44 |
| silver | slv_product_history / slv_store_history / slv_product_conflicts | table | 848 / 264 / 1 |
| gold | fct_sales_line | table | 231,122 |
| gold | dim_product / dim_store / dim_region / dim_date | table | 43 / 13 / 5 / 1,461 |

Reconciliation: 232,050 landed − 187 quarantined − 741 duplicate versions collapsed (retries + corrections)
= **231,122** lines in the fact.

### Quickest check – no extra install

`make inspect` uses the DuckDB library already installed by `make setup` and prints the table above,
the reconciliation line and quarantine by reason. Same command is in the README for reviewers.

### Three ways to open it on a Mac (optional SQL workbench)

**1. DuckDB browser UI (easiest)**
```bash
brew install duckdb
cd ~/projects/SigmoidCaseStudy
duckdb -ui data/warehouse/cpg.duckdb
```
A browser tab opens: schemas and tables on the left; click to preview or run SQL.

**2. DuckDB in the terminal**
```bash
cd ~/projects/SigmoidCaseStudy
duckdb data/warehouse/cpg.duckdb
```
```sql
SHOW ALL TABLES;
SELECT * FROM gold.dim_store WHERE store_code = 'S003';
SELECT dq_reason, count(*) FROM silver.slv_sales_quarantine GROUP BY 1;
.quit
```

**3. DBeaver (GUI SQL client)**

1. **Database → New Database Connection → DuckDB → Next.**
2. **Path:** browse to `~/projects/SigmoidCaseStudy/data/warehouse/cpg.duckdb`.
3. Tick **Read-only connection** (Connection settings → General). Read-only never locks the file, so
   `make` can rebuild while DBeaver is open (refresh with F5 afterwards).
4. **Bronze views need one setting** – they read the CSVs via a relative path. Under
   **Connection settings → Initialization → Bootstrap queries**, add:
   ```sql
   SET file_search_path = '/Users/ashok/projects/SigmoidCaseStudy';
   ```
   Without it silver and gold work, but opening a bronze view fails with "No files found".
5. **Finish.** If DBeaver offers to download the DuckDB driver, accept.
6. Expand **cpg → ref / bronze / silver / gold** to browse tables, or open an SQL editor (Ctrl/Cmd + ]).

**If it fails with a "storage version" / "unsupported version" error:** DBeaver's bundled DuckDB driver
is older than the DuckDB that built the file (1.5.6). Fix: **Database → Driver Manager → DuckDB → Edit →
Libraries → Download/Update** to the latest `duckdb_jdbc`, then reconnect.

**Why not Docker here?** DuckDB needs no installation (it is a Python library pinned in
`requirements.txt`). The containerised run path the PDF requires (*"Provide a deployment or
containerized run path"*) is built in **Block 4** together with CI; `make inspect` will work inside it too.

**Notes**
- Start from inside the project folder: bronze **views** read the CSVs through a relative path and fail
  from elsewhere (silver and gold tables work anywhere).
- Close the UI/CLI (or use a read-only connection, as in DBeaver above) before rebuilding – DuckDB allows one writer at a time.

## How you can verify it yourself

```bash
make setup             # once: creates .venv with pinned versions
make all               # history: expect "PASS=52 WARN=0"
make demo-incremental  # October: expect "PASS=51 WARN=1"
make inspect           # all schemas/tables with row counts + reconciliation + quarantine by reason
make preview TABLE=gold.dim_store          # first 20 rows of any table or view (ROWS=50 for more)
make query SQL="select * from silver.slv_dq_batch_summary where batch_id >= '2026-09'"
```

`preview` and `query` are read-only shortcuts over the same DuckDB library – no install, and they
set the folder for bronze views automatically.

Then look at any table:

```bash
.venv/bin/dbt show --project-dir dbt --profiles-dir dbt --inline "select dq_reason, count(*) n from silver.slv_sales_quarantine group by 1 order by 2 desc"
.venv/bin/dbt show --project-dir dbt --profiles-dir dbt --inline "select store_code, region_code, valid_from, valid_to from gold.dim_store where store_code = 'S003'"
.venv/bin/dbt show --project-dir dbt --profiles-dir dbt --inline "select region_code_at_sale, min(event_date_local), max(event_date_local), count(*) from gold.fct_sales_line where store_code = 'S003' group by 1"
.venv/bin/dbt show --project-dir dbt --profiles-dir dbt --inline "select * from silver.slv_dq_batch_summary where batch_id >= '2026-09'"
```

## Not in this block
Metric definitions, forecast, AI (Blocks 3–4); Docker and CI (Block 4); written docs, ADRs, diagrams (Block 5).

## Assumptions agreed for this block

| # | Assumption | Alternative | Confirm with |
|---|---|---|---|
| 1 | Corrections / late data **> 14 days** after month close are **held for Finance** | Apply automatically | Finance |
| 2 | Region reporting **as-was** by default | As-is | Sales Ops |
| 3 | **ERP wins** when ERP and PIM disagree | PIM wins for some fields | Master Data |
| 4 | Reporting currency **INR**, monthly average FX | Daily rate / USD | Finance |
| 5 | Fiscal year starts **April**, 4-4-5 periods | Calendar year | Finance |
| 6 | **Monthly** batches in PoC (daily in production) | Daily files | Data Platform |
