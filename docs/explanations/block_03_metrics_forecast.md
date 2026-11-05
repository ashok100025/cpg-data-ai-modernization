# Block 3 – One set of metric definitions, and the forecast

**Status:** explained 2026-11-05 09:45; built and verified locally 19:39–19:50 IST; reviewed by Ashok
21:17–21:55; pushed on approval.

**In one line:** define revenue and demand **once**, make every consumer use that single definition,
and produce a backtested weekly forecast from it.

---

## Why this block (PDF links)

| PDF says | Where |
|---|---|
| *"Reporting teams maintain separate metric definitions"*, *"without creating separate definitions of the same measures"* | Page 1 – the client's core pain |
| *"Business teams need trusted measures of revenue and demand"* | Page 1 |
| *"Enable governed analytics and revenue forecasting"* | Problem area 3 |
| *"At least one analytics or forecast output is calculated from actual data, with defined grain, assumptions, and validation"* | Page 2, functional requirement #3 |
| *"Advanced ML not required; explain model suitability, leakage risk, and measurement instead"* | Page 2, "What is NOT required" |
| *"A requirements trace links business questions to … measures … consumers"* | Page 2 – the metric catalogue is the "measures" link; dbt exposures are the "consumers" link |

## How – four steps

### Step 1 – Metric catalogue (`metrics/metrics.yml`)
Each measure written **once**, with meaning, formula, owner, unit and sensitivity.

| Metric | Definition | Owner | Sensitivity |
|---|---|---|---|
| `gross_sales` | Value sold before returns (INR, tax excluded) | Finance | internal |
| `returns_value` | Value returned/refunded | Finance | internal |
| `net_revenue` | gross_sales − returns – **the** revenue measure | Finance | internal |
| `units_sold`, `units_returned` | Unit counts | Supply Chain | internal |
| `net_units` | units sold − returned – **the** demand measure | Supply Chain | internal |
| `return_rate` | returns_value ÷ gross_sales (ratio) | Finance | internal |
| `avg_selling_price` | net_revenue ÷ net_units (ratio) | Commercial | commercially sensitive |
| `promo_revenue` | net revenue sold on promotion | Trade Marketing | commercially sensitive |
| `promo_revenue_share` | promo_revenue ÷ net_revenue (ratio) | Trade Marketing | commercially sensitive |

**Allowed dimensions (12):** week, month, fiscal_year, fiscal_period, **region (as-was)**,
**region_as_is**, **category (as-was)**, **category_as_is**, brand, channel, store, sku.
Sensitivity labels are defined here and **enforced in Block 4** (who may see what).

### Step 2 – Metric compiler (`src/poc/metrics.py`)
The **only** code allowed to turn metric names into SQL. Input: metrics + dimensions + filters +
date range. Output: SQL plus parameters plus metadata (owner, unit, sensitivity per metric).
Guarantees:
- refuses unknown metrics, dimensions, filters, bad dates (`MetricError`) – nothing is guessed
- filter values are **bound parameters**, never pasted into SQL (an injection attempt returns 0 rows)
- ratio metrics are built from their base metrics' formulas, so they cannot drift
- a join is added only when a requested dimension needs it – no double counting

Three consumers use it: the weekly mart, the forecast, and (Block 4) the AI assistant.
Production equivalent: Unity Catalog metric views.

### Step 3 – Weekly mart (`gold.mart_sales_weekly`)
Grain **week × region (as-was) × category (as-was) × channel**, all metrics. Built as a **dbt Python
model** that calls the compiler – stays inside dbt's build order, tests and lineage while every formula
comes from the YAML. Ratios are correct at this grain only (never sum them across rows).
**dbt exposures** declare its consumers (forecast, AI assistant, sales reporting) so lineage shows
who depends on what.

### Step 4 – Forecast (`src/poc/forecast.py`)
- **What:** weekly `net_revenue` and `net_units`, **category × region**, **as-is**, 8 weeks ahead
  (25 series, 90 weeks of history to week of 21 Sep 2026).
- **Why as-is:** future sales happen in today's structure – S003's history counts toward WEST.
- **Models:** (1) **seasonal naive** = same week last year – the baseline; (2) **seasonal naive × recent
  trend** = last year's week scaled by last 8 weeks vs the same 8 weeks a year earlier (clipped 0.5–2.0).
- **Validation:** rolling-origin **backtest** – 4 origins over the last ~4 months, horizons 1–8;
  **WAPE**, **bias**, **forecast value added (FVA)** vs baseline; lowest WAPE per measure is selected.
- **Confidence per series:** high (< 20% WAPE), medium (20–35%), low (> 35%) – shown next to every
  forecast value.
- **Leakage guards:** models receive only the past (array slice); a test independently re-forecasts every
  stored backtest point from strictly earlier data; partial weeks are never used or scored.

---

# Exact inventory – what Block 3 created

| # | Object | Type / purpose |
|---|---|---|
| 1 | `metrics/metrics.yml` | Metric catalogue – 10 metrics, 12 dimensions, 4 joins, 2 sensitivity levels |
| 2 | `src/poc/metrics.py` | Metric compiler (`MetricCatalog`, `MetricError`, `CompiledQuery`) |
| 3 | `dbt/models/marts/mart_sales_weekly.py` | dbt Python model → `gold.mart_sales_weekly` |
| 4 | `dbt/models/marts/_marts.yml` | Mart tests + 3 **exposures** (revenue_forecast, ai_insight_assistant, sales_reporting) |
| 5 | `dbt/macros/test_unique_mart_grain.sql` | Generic test: one row per mart grain |
| 6 | `dbt/tests/assert_mart_reconciles_to_fact.sql` | Mart totals = fact totals |
| 7 | `dbt/dbt_project.yml` (update) | `marts` folder → schema `gold` |
| 8 | `src/poc/forecast.py` | Backtest + forecast → 4 tables below |
| 9 | `tests/conftest.py`, `tests/test_metrics.py`, `tests/test_forecast.py` | 26 pytest tests |
| 10 | `Makefile` (update) | `make forecast`, `make test`, **`make sql`** (added after review); `make all` = data → build → forecast → test; demo re-forecasts |
| 11 | README, this file, glossary, methodology logs | Documentation |

**New tables in `gold`:**

| Table | Grain | Rows (history run) |
|---|---|---|
| `mart_sales_weekly` | week × region × category × channel | 3,475 |
| `forecast_backtest` | measure × model × origin × series × forecast week | ~5,200 |
| `forecast_accuracy` | measure × model (WAPE, bias, FVA, is_selected) | 4 |
| `forecast_series_accuracy` | measure × series (WAPE, bias, confidence) | 50 |
| `forecast_weekly` | run × measure × model × series × future week (+ is_selected, confidence) | 800 |

---

## Verification results (history run, `make all`)

| Check | Result |
|---|---|
| dbt build | ✅ 59 tests pass, 0 warnings (3 exposures registered) |
| Python tests | ✅ 26 pass |
| Compiler totals through every one of 12 dimensions = fact total | ✅ (no join double-counts) |
| Mart = compiler output, row for row | ✅ |
| As-is minus as-was for WEST = S003's sales before 1 Jul 2026 | ✅ exactly |
| Injection attempt in a filter | ✅ bound parameter, 0 rows |
| Forecast – net revenue | trend model **WAPE 14.5%**, bias +3.4%, **FVA +22.5%** vs naive (WAPE 18.8%, bias −15.4%) |
| Forecast – net units | trend model **WAPE 12.6%**, bias +2.3%, **FVA +30.3%** vs naive (18.1%, −15.9%) |
| Accuracy by horizon (revenue) | 12–16% across weeks 1–8 – no collapse at longer horizons |
| Series confidence | 19 high · 4 medium · 2 low (Healthy Snacks EAST, UAE) |
| **Deliberate leak** (backtest sees one extra week) | ✅ `test_stored_backtest_used_only_data_before_each_origin` **fails**; passes on real code |
| October demo (`make demo-incremental`) | ✅ 58 pass + 1 expected warning; forecast re-runs on 94 weeks; 26 tests pass |

Why the naive model under-forecasts by ~15%: the business grows (~6%/yr in stores, ~25%/yr e-commerce)
and same-week-last-year ignores growth. The trend factor corrects that – this is what "model suitability"
means in the PDF: the simplest model that captures the main pattern, proven better than the baseline.

## Changes made during the build (AI output corrected)

| What | Why |
|---|---|
| YAML key `on:` renamed to `condition:` | PyYAML reads `on` as boolean `True` – join conditions vanished (C7) |
| Per-series confidence labels added | Overall WAPE 14.5% hid 30–64% error on the single-product Healthy Snacks series (C9) |
| New test re-forecasting every stored backtest point | The first tests did **not** catch a deliberately leaked backtest loop; now they do (C8) |
| Generic test renamed to `unique_mart_grain` | Clearer name |

## How you can verify it yourself

```bash
make all                     # expect: 59 dbt tests pass, forecast table printed, "26 passed"
make preview TABLE=gold.mart_sales_weekly
make preview TABLE=gold.forecast_accuracy
make query SQL="select category, region, confidence, round(wape*100,1) wape_pct from gold.forecast_series_accuracy where measure='net_revenue' order by wape desc"
make query SQL="select week, region, round(sum(forecast)) net_revenue_fc from gold.forecast_weekly where is_selected and measure='net_revenue' group by 1,2 order by 1,2"
```

## Assumptions agreed for this block

| # | Assumption | Alternative | Confirm with |
|---|---|---|---|
| 1 | **Demand = net units sold** (observed; stock-outs invisible without inventory) | Unconstrained demand (needs inventory feed) | Supply Chain |
| 2 | Forecast grain week × category × region, 8-week horizon | SKU × store (too sparse) | Demand Planning |
| 3 | Forecast **as-is**; reporting **as-was** | As-was for both | Sales Ops + Planning |
| 4 | Simple statistical models only | Prophet / gradient boosting | Data Science lead |
| 5 | Backtest over the last ~4 months, 4 origins | Longer window (only 90 weeks exist) | Data Science lead |

## Not in this block
AI assistant and enforcement of sensitivity (Block 4); Docker and CI (Block 4); written models, ADRs,
architecture diagram (Block 5).

---

# Questions from review (2026-11-05)

## Q1. Are all 12 dimensions in `metrics.yml` separate tables?

No. A **dimension** is a way to slice a number ("by week", "by region") – a *column*, not a table.
The 12 dimensions come from **3 dimension tables plus columns already on the fact**:

| Dimension | Comes from | How |
|---|---|---|
| week, month, fiscal_year, fiscal_period | `dim_date` | join on `date_key` |
| category, brand | `dim_product` – version **at sale time** (as-was) | join on `product_sk` |
| category_as_is | `dim_product` – **current** version | joined again, by `sku` + `is_current` |
| region_as_is | `dim_store` – **current** version | join by `store_code` + `is_current` |
| region (as-was) | fact column `region_code_at_sale` | no join – stamped on each sale in Block 2 |
| channel, store, sku | fact columns | no join |

4 joins, 3 tables: `dim_product` is joined twice in two roles – *product as it was* (`product`) and
*product as it is now* (`product_now`).

## Q2. How was `metrics.yml` designed – the raw thinking

Start from a business question and break it into parts:

> *"What was **net revenue** **by region** **last quarter**?"*

| Part of the question | What the system must know | Section |
|---|---|---|
| "net revenue" | The formula, over which rows | `metrics` |
| "by region" | Where region lives (column or join) | `dimensions` |
| "last quarter" | Which date column to filter on | `source.date_column` |
| all of it | Which table the numbers come from and how to reach dimension tables | `source.fact` + `source.joins` |

- **`source` – the physical wiring:** the `FROM` and `JOIN` part of the SQL. One fact table because every
  metric is about sales lines (star schema). Kept separate so that **if tables move (e.g. to Databricks),
  only `source` changes** – the business vocabulary stays.
- **`dimensions` – the slicing vocabulary:** name → SQL expression → join needed (if any).
- **`metrics` – the measure vocabulary:** name → formula + owner, unit, sensitivity, certified.
  **Ratios** are numerator ÷ denominator of other metrics, because a ratio must be *sum ÷ sum* –
  averaging row-level ratios gives the wrong answer.

The question above compiles to:
```sql
select f.region_code_at_sale as region,                       -- dimensions.region.expr
       sum(f.net_sales_inr)  as net_revenue                    -- metrics.net_revenue.expr
from gold.fct_sales_line f                                     -- source.fact
where f.event_date_local >= ? and f.event_date_local <= ?      -- source.date_column (+ bound values)
group by 1
```
Asking "by category" makes the compiler add `left join gold.dim_product product on …` from `source.joins`.

## Q3. Why is a file in `models/marts/` a gold table, and why Python?

**Folder ≠ schema.** dbt folders only organise files; the schema comes from config. `dbt_project.yml`
has `marts: +schema: gold`, so `models/marts/mart_sales_weekly.py` → `gold.mart_sales_weekly`.
Two kinds of gold are kept in separate folders:
- `models/gold/` – the **curated model** (fact + dimensions, contract-protected) – the source of truth
- `models/marts/` – **consumption tables derived from metrics**, shaped for a use case

**Why Python:** a dbt SQL model cannot call the Python compiler.

| Option | Problem |
|---|---|
| SQL mart writing `sum(net_sales_inr)` itself | A second definition of revenue – the client's exact problem |
| Script generating SQL files from the YAML | Extra step; files can go stale |
| **dbt Python model calling the compiler** ✅ | One definition, still in dbt's build order, tests and lineage |

In production, Unity Catalog **metric views** hold the definitions and a plain SQL mart queries them.

## Q4. What does `mart_sales_weekly.py` actually do – where is the GROUP BY?

The file never writes SQL; it **asks the compiler**. Five steps:

1. **dbt runs the file** – calls `model(dbt, session)`; `session` is an open DuckDB connection.
2. **Load the catalogue** – `MetricCatalog.load()` → `metrics.py` line 53 `yaml.safe_load` reads
   `metrics.yml`; the constructor (line 41) keeps fact, joins, dimensions, metrics; `_validate()`
   (line 56) checks every metric has owner/sensitivity and every ratio points to real metrics.
3. **Say *what*, not *how*** – `catalog.compile(metrics=[10 names], dimensions=["week","region","category","channel"])`.
4. **`compile()` writes the SQL** – `metrics.py` lines 83–135:

| Lines | What it does | Uses from metrics.yml |
|---|---|---|
| 92–101 | Refuse unknown metric / dimension names | `metrics`, `dimensions` |
| 103–107 | Work out needed joins (week → date, category → product; region, channel → none) | `dimensions.*.join` |
| 109 | SELECT for dimensions (`date.week_start as week`, …) | `dimensions.*.expr` |
| 110 + 75–81 | SELECT for metrics; ratios built by `metric_expr()` as numerator ÷ denominator | `metrics.*.expr`, `numerator`, `denominator` |
| 111 | `from gold.fct_sales_line f` | `source.fact` |
| 112–113 | `left join …` per needed join | `source.joins` |
| 115–127 | WHERE with `?` placeholders (none for the mart) | `source.date_column` |
| 128–131 | **`group by 1, 2, 3, 4`** – one number per dimension | number of dimensions |
| 135 | Return SQL + parameters + metadata | |

5. **Run and save** – `return session.sql(q.sql)`; DuckDB runs it and dbt writes `gold.mart_sales_weekly`
   (3,475 rows), then runs its tests.

The SQL generated for the mart:
```sql
select
    date.week_start as week,                    -- dimension "week"     (join: date)
    f.region_code_at_sale as region,            -- dimension "region"   (fact column)
    product.category_name as category,          -- dimension "category" (join: product)
    f.channel as channel,                       -- dimension "channel"  (fact column)
    sum(f.gross_sales_inr) as gross_sales,      -- metric expr copied from YAML
    sum(f.returns_inr) as returns_value,
    sum(f.net_sales_inr) as net_revenue,
    sum(f.units_sold) as units_sold,
    sum(f.units_returned) as units_returned,
    sum(f.qty) as net_units,
    sum(case when f.on_promotion then f.net_sales_inr else 0 end) as promo_revenue,
    (sum(f.returns_inr)) / nullif(sum(f.gross_sales_inr), 0) as return_rate,          -- returns_value / gross_sales
    (sum(f.net_sales_inr)) / nullif(sum(f.qty), 0) as avg_selling_price,             -- net_revenue / net_units
    (sum(case when f.on_promotion then f.net_sales_inr else 0 end))
        / nullif(sum(f.net_sales_inr), 0) as promo_revenue_share                     -- promo_revenue / net_revenue
from gold.fct_sales_line f                                                -- source.fact
left join gold.dim_date date on f.date_key = date.date_key                -- source.joins.date
left join gold.dim_product product on f.product_sk = product.product_sk   -- source.joins.product
group by 1, 2, 3, 4
order by 1, 2, 3, 4
```

The forecast and (Block 4) the AI assistant call the **same** `compile()`: if Finance changes
`net_revenue` in `metrics.yml`, all three change together on the next run.

## Q5. What is WAPE?

**Weighted Absolute Percentage Error** = total absolute error ÷ total actual.

| Week | Actual | Forecast | Absolute error |
|---|---|---|---|
| 1 | 100 | 90 | 10 |
| 2 | 200 | 230 | 30 |
| 3 | 100 | 100 | 0 |
| **Total** | **400** | | **40** |

WAPE = 40 ÷ 400 = **10%** – "on average the forecast misses by 10% of sales".
Not MAPE (average of each week's % error): MAPE explodes on small weeks (actual 2, forecast 4 = 100%)
and breaks on zero weeks. WAPE weights by volume = error in rupee terms. WAPE has no direction, so
**bias** is reported too: naive −15% (under-forecasts, ignores growth); trend model +3% (close to neutral).

## Q6. What do the three verification commands show?

| Command | What it proves | What to look for |
|---|---|---|
| `make all` | The whole pipeline in one command: data → bronze/silver/gold/mart → forecast → tests (PDF: *"another engineer can run the PoC and reproduce its outputs"*) | `PASS=59 WARN=0`; forecast accuracy lines (trend model **selected**, beats naive); confidence summary; `26 passed` |
| `make preview TABLE=gold.forecast_accuracy` | Forecast **validation** (PDF: *"with defined grain, assumptions, and validation"*) | 4 rows (2 measures × 2 models); trend model lower WAPE → `is_selected = true`; `fva_vs_naive` = how much better |
| `make query … forecast_series_accuracy` | **Which forecasts to trust** | Worst first: Healthy Snacks EAST/UAE `low`; the rest high/medium |

The forecast itself (next 8 weeks, net revenue per region):
```bash
make query SQL="select week, region, round(sum(forecast)) as net_revenue_forecast from gold.forecast_weekly where is_selected and measure='net_revenue' group by 1,2 order by 1,2"
```

## Q7. How can I see the SQL for any metric request?

`make sql` (added after this review) prints what the compiler generates – the only place metric SQL is created:
```bash
make sql METRICS=net_revenue,return_rate BY=region,week WHERE="category=Snacks"
make sql METRICS=profit_margin BY=region      # -> REFUSED: unknown metric(s) ...
```
