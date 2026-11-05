# Appendix – Glossary

Definitions and full forms used across the case study. Kept alphabetical; new terms are added as
they come up.

| Term | Full form | Meaning in this project |
|---|---|---|
| **4-4-5 calendar** | – | Retail/fiscal calendar: each 13-week quarter is split into periods of 4, 4 and 5 **whole weeks**, so every period has the same weekdays and weekends and year-on-year comparisons are fair. 52 weeks a year, with a 53rd week every 5–6 years. Variants: 4-5-4, 5-4-4. Which one the client uses is confirmed with Finance. |
| **ADR** | Architecture Decision Record | Short document recording one important decision: context, options, decision, consequences, validation needed before production. The PDF requires at least two (`docs/adr/`). |
| **Anomaly-based alert** | – | An alert that compares a value with its own recent baseline (e.g. 3× the trailing 6-batch average) instead of a fixed limit. Fires on real incidents, stays quiet on normal variation. |
| **As-is / As-was** | – | Two ways to report history when an attribute changes. **As-was**: a sale keeps the attribute valid on the sale date (June sale of S003 stays SOUTH) – reporting default, closed numbers never change. **As-is**: all history is shown with today's attribute (all S003 sales shown in WEST) – used for like-for-like planning and the **forecast**, because future sales happen in the current structure. |
| **Backtest** | – | Testing a forecast on the past: pretend it is an earlier date, forecast forward using only data before that date, and compare with what actually happened. *Rolling-origin* = repeated at several cut-off dates. |
| **Bias (forecast)** | – | Whether a forecast is systematically too high (+) or too low (−): (forecast − actual) ÷ actual, summed. |
| **Bronze / Silver / Gold** | Medallion architecture | Data layers. **Bronze** = raw, as received. **Silver** = cleaned, typed, de-duplicated, validated. **Gold** = business-ready facts and dimensions for reporting, forecasting and AI. |
| **Business key** | – | The identifier that makes a record unique in business terms (here: source system + transaction id + line number). Used to de-duplicate and apply corrections. |
| **Confidence label** | – | High / medium / low tag on each forecast series from its own backtest WAPE (< 20%, 20–35%, > 35%), so consumers know which numbers to trust. |
| **Correction** | – | A source re-sends a record it already sent, with changed values (e.g. corrected quantity). Same business key, later ingestion time; the latest version wins. |
| **CPG** | Consumer Packaged Goods | Everyday packaged products bought often – drinks, snacks, shampoo, detergent (e.g. HUL, ITC, Nestlé, P&G). The client in the case study is a mid-size CPG company. |
| **Data contract** | – | A written, enforced agreement for a dataset: columns and types, meaning, keys, owner, freshness, quality guarantees and how changes are made. Breaking it fails the build. |
| **dbt** | data build tool | Open-source tool to build data transformations as SQL models with tests, documentation, lineage and contracts. Used in the PoC; also runs on Databricks and Snowflake. |
| **dbt exposure** | – | A declaration in dbt of who consumes the data (dashboard, ML model, application). Shows consumers in the lineage graph. |
| **dbt Python model** | – | A dbt model written in Python instead of SQL; still part of dbt's build order, tests and lineage. Used for the weekly mart so it can call the metric compiler. |
| **DuckDB** | – | A small, fast analytical database that runs inside a process on a laptop – no server. PoC substitute for Databricks. |
| **ERP** | Enterprise Resource Planning | The company's core operational system for finance, procurement, manufacturing, inventory and the **material (product) master** – e.g. SAP, Oracle, Microsoft Dynamics. In this project the ERP is the owner of product identity, pack size, launch date and lifecycle status. |
| **FVA** | Forecast Value Added | How much a model improves on the baseline: 1 − WAPE(model) ÷ WAPE(baseline). Positive = the model earns its complexity. |
| **FX** | Foreign Exchange | Currency conversion rate. UAE sales in AED are converted to INR at the monthly average FX rate. |
| **Grain** | – | What one row of a table represents. Here the sales fact's grain is *one sale or return line event*. Defining the grain first prevents double counting. |
| **Incremental load** | – | Processing only data that arrived since the last run, instead of rebuilding everything. Must give exactly the same result as a full rebuild. |
| **Leakage (data leakage)** | – | When a model is trained or tested with information it would not have had at forecast time (future values, later-arriving data). Makes accuracy look better than it really is. |
| **Lineage** | – | The ability to trace any number back through each transformation to the source file it came from. |
| **Mart** | Data mart | A consumption-ready table shaped for a use case (here: weekly sales by region, category, channel). |
| **Metric catalogue / semantic layer** | – | The single place where business measures are defined (formula, owner, meaning). Consumers ask for metrics by name instead of writing their own SQL. Here: `metrics/metrics.yml` + compiler; in production: Unity Catalog metric views. |
| **PIM** | Product Information Management | System used by marketing/e-commerce to manage product content – brand, category, descriptions, images. Here it owns brand and category. |
| **POS** | Point of Sale | The billing system at a store's checkout counter. One of our two sales sources. |
| **Quarantine** | – | A table holding rows that failed a quality rule, with the reason. Bad data is kept and visible, never silently dropped, and can be replayed once fixed. |
| **Restatement** | – | Officially changing numbers of a period that is already closed and reported. Done through a controlled Finance process, never silently by a pipeline. |
| **Retry (duplicate)** | – | A source sends the exact same record again (e.g. after a network timeout). Must be collapsed to one row, never counted twice. |
| **SCD2** | Slowly Changing Dimension, Type 2 | A way to keep history of changing attributes: instead of overwriting, the old row is closed (valid_to) and a new row is opened (valid_from). Used for product category and store region. |
| **Seasonal naive** | – | Forecast = the value of the same week last year. The standard baseline any forecast model must beat. |
| **Seed** | – (dbt term) | A small CSV file kept in the repo and loaded as a table by dbt – used for reference data we own (regions, FX rates, id mappings). |
| **SKU** | Stock Keeping Unit | The unique code for one sellable product variant (e.g. a specific juice in a 1-litre pack). |
| **Surrogate key (`_sk`)** | – | A system-generated key for a dimension row (one per version in SCD2), e.g. `product_sk`. Facts link to it, so a sale points to the exact product version valid on the sale date. |
| **Survivorship rule** | – | When two systems hold the same attribute, the rule that decides whose value wins (here: ERP for pack size/status, PIM for brand/category). |
| **WAPE** | Weighted Absolute Percentage Error | Total absolute forecast error ÷ total actual. 14.5% = on average the forecast is off by 14.5% of actual sales. Weighted, so big series dominate – hence per-series confidence too. |
