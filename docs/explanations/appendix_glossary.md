# Appendix – Glossary

Definitions and full forms used across the case study. Kept alphabetical; new terms are added as
they come up.

| Term | Full form | Meaning in this project |
|---|---|---|
| **4-4-5 calendar** | – | Retail/fiscal calendar: each 13-week quarter is split into periods of 4, 4 and 5 **whole weeks**, so every period has the same weekdays and weekends and year-on-year comparisons are fair. 52 weeks a year, with a 53rd week every 5–6 years. Variants: 4-5-4, 5-4-4. Which one the client uses is confirmed with Finance. |
| **Accounting month** | – | The month a line counts in Finance's books. Normally the sale month; for a late line booked under BOOK_IN_CURRENT, the booking month. Column `accounting_month` on the fact. |
| **Adjustment line** | – | A separate fact line holding only the difference when a late correction is booked in a later month, so the closed month keeps its figure. |
| **ADLS Gen2** | Azure Data Lake Storage Gen2 | Azure's storage for data lakes; holds the Delta tables and landing files. |
| **ADR** | Architecture Decision Record | Short document recording one important decision: context, options, decision, consequences, validation needed before production. The PDF requires at least two (`docs/adr/`). |
| **Anomaly-based alert** | – | An alert that compares a value with its own recent baseline (e.g. 3× the trailing 6-batch average) instead of a fixed limit. Fires on real incidents, stays quiet on normal variation. |
| **As-is / As-was** | – | Two ways to report history when an attribute changes. **As-was**: a sale keeps the attribute valid on the sale date (June sale of S003 stays SOUTH) – reporting default, closed numbers never change. **As-is**: all history is shown with today's attribute (all S003 sales shown in WEST) – used for like-for-like planning and the **forecast**, because future sales happen in the current structure. |
| **Audit log** | – | Append-only record of every request: who asked, what, the decision, the query fingerprint. Here `outputs/audit/insight_audit.jsonl`; in production Unity Catalog system tables. |
| **Auto Loader** | – | Databricks feature that ingests only new files from storage, with schema evolution. |
| **Backtest** | – | Testing a forecast on the past: pretend it is an earlier date, forecast forward using only data before that date, and compare with what actually happened. *Rolling-origin* = repeated at several cut-off dates. |
| **Bias (forecast)** | – | Whether a forecast is systematically too high (+) or too low (−): (forecast − actual) ÷ actual, summed. |
| **Blue/green deployment** | – | Build the new version beside the old one, validate it, then switch consumers over in one step; switch back if needed. |
| **BOOK_IN_CURRENT / RESTATE** | – | Finance's two restatement decisions: put late lines into the current open month (closed month unchanged), or back into their own sale month (closed month gets a new version). |
| **Bronze / Silver / Gold** | Medallion architecture | Data layers. **Bronze** = raw, as received. **Silver** = cleaned, typed, de-duplicated, validated. **Gold** = business-ready facts and dimensions for reporting, forecasting and AI. |
| **Business key** | – | The identifier that makes a record unique in business terms (here: source system + transaction id + line number). Used to de-duplicate and apply corrections. |
| **CI** | Continuous Integration | Automatic build and test on every push / pull request (here GitHub Actions). A failing check blocks the change. |
| **CODEOWNERS** | – | GitHub file naming who must review changes to which paths – makes ownership enforceable. |
| **Completeness signal** | – | A number telling a consumer how complete an official figure is – here the late sales still pending restatement, shown next to answers. |
| **Conceptual / logical / physical model** | – | Three levels of data modelling: **conceptual** = business entities and relationships; **logical** = keys, attributes, grain, history, database-independent; **physical** = real tables, columns, types, storage choices. |
| **Confidence label** | – | High / medium / low tag on each forecast series from its own backtest WAPE (< 20%, 20–35%, > 35%), so consumers know which numbers to trust. |
| **Container / Docker** | – | A packaged, isolated runtime with the exact OS, Python and libraries; `docker run` behaves the same on any machine. |
| **Correction** | – | A source re-sends a record it already sent, with changed values (e.g. corrected quantity). Same business key, later ingestion time; the latest version wins. |
| **CPG** | Consumer Packaged Goods | Everyday packaged products bought often – drinks, snacks, shampoo, detergent (e.g. HUL, ITC, Nestlé, P&G). The client in the case study is a mid-size CPG company. |
| **Data contract** | – | A written, enforced agreement for a dataset: columns and types, meaning, keys, owner, freshness, quality guarantees and how changes are made. Breaking it fails the build. |
| **Data diff** | – | Comparing a new build's tables with the current production tables (row counts, totals) before releasing. |
| **Databricks Asset Bundles (DABs)** | – | Databricks' way to define jobs, pipelines and settings as code and deploy them per environment from CI. |
| **dbt** | data build tool | Open-source tool to build data transformations as SQL models with tests, documentation, lineage and contracts. Used in the PoC; also runs on Databricks and Snowflake. |
| **dbt exposure** | – | A declaration in dbt of who consumes the data (dashboard, ML model, application). Shows consumers in the lineage graph. |
| **dbt Python model** | – | A dbt model written in Python instead of SQL; still part of dbt's build order, tests and lineage. Used for the weekly mart so it can call the metric compiler. |
| **Definition of done** | – | The checklist a change must meet before it counts as finished (tests, docs, review, CI green). |
| **Delta Lake** | – | Open table format on files: ACID transactions, MERGE, schema evolution, time travel. |
| **DuckDB** | – | A small, fast analytical database that runs inside a process on a laptop – no server. PoC substitute for Databricks. |
| **ER diagram** | Entity–Relationship diagram | Picture of entities (boxes) and how they relate (lines with cardinality: one, many, optional). |
| **ERP** | Enterprise Resource Planning | The company's core operational system for finance, procurement, manufacturing, inventory and the **material (product) master** – e.g. SAP, Oracle, Microsoft Dynamics. In this project the ERP is the owner of product identity, pack size, launch date and lifecycle status. |
| **FinOps** | Financial Operations | Practice of managing cloud cost: tagging, budgets, auto-stop, right-sizing, regular review. |
| **FVA** | Forecast Value Added | How much a model improves on the baseline: 1 − WAPE(model) ÷ WAPE(baseline). Positive = the model earns its complexity. |
| **FX** | Foreign Exchange | Currency conversion rate. UAE sales in AED are converted to INR at the monthly average FX rate. |
| **Golden set (AI eval)** | – | A fixed list of questions with the expected outcome (answer / refuse) run automatically, so a change that makes the AI behave worse fails the build. |
| **Grain** | – | What one row of a table represents. Here the sales fact's grain is *one sale or return line event*. Defining the grain first prevents double counting. |
| **Grounding** | – | An AI answer is grounded when every fact in it comes from an approved source – here every number comes from the query result, which comes from certified metrics. |
| **Guardrails** | – | Deterministic checks around an AI component that it cannot override: catalogue validation, access policy, forced filters, row caps. |
| **Handoff classification** | – | How ready a component is to give to a receiving team: PoC-only, prototype, or production-candidate. |
| **Idempotent** | – | Running the same job again gives the same result. Proven here by repeated incremental runs and a full rebuild producing the same content hash. |
| **Incremental load** | – | Processing only data that arrived since the last run, instead of rebuilding everything. Must give exactly the same result as a full rebuild. |
| **Lakeflow** | – | Databricks' ingestion (Lakeflow Connect), pipeline (Lakeflow Declarative Pipelines, formerly DLT) and orchestration (Lakeflow Jobs) products. |
| **Leakage (data leakage)** | – | When a model is trained or tested with information it would not have had at forecast time (future values, later-arriving data). Makes accuracy look better than it really is. |
| **Lineage** | – | The ability to trace any number back through each transformation to the source file it came from. |
| **Liquid clustering** | – | Delta feature that organises data by chosen columns (e.g. date, store, SKU) so queries scan less. |
| **LLM** | Large Language Model | AI model that works with text (e.g. Claude). Here only allowed to translate a question into a plan. |
| **Mart** | Data mart | A consumption-ready table shaped for a use case (here: weekly sales by region, category, channel). |
| **Materiality** | – | The size of an error below which Finance does not reopen a closed period (often a % of revenue); decides RESTATE vs BOOK_IN_CURRENT ([A-20](../requirements/assumptions_register.md#a-20)). |
| **Mermaid** | – | Text syntax for diagrams inside markdown; GitHub renders it as a picture. |
| **Metric catalogue / semantic layer** | – | The single place where business measures are defined (formula, owner, meaning). Consumers ask for metrics by name instead of writing their own SQL. Here: `metrics/metrics.yml` + compiler; in production: Unity Catalog metric views. |
| **Mutation testing** | – | Breaking the code on purpose to prove a test fails when it should. |
| **OIDC federation** | OpenID Connect | Lets CI log in to Azure with short-lived tokens instead of stored passwords or keys. |
| **PIM** | Product Information Management | System used by marketing/e-commerce to manage product content – brand, category, descriptions, images. Here it owns brand and category. |
| **POS** | Point of Sale | The billing system at a store's checkout counter. One of our two sales sources. |
| **Private endpoint** | – | Network interface that makes an Azure service reachable only from your private network, not the internet. |
| **Prompt injection** | – | Text in a request that tries to make the AI ignore its rules ("ignore your instructions…"). Refused here; and even a fooled planner cannot get past the guardrails. |
| **Quarantine** | – | A table holding rows that failed a quality rule, with the reason. Bad data is kept and visible, never silently dropped, and can be replayed once fixed. |
| **RACI** | Responsible, Accountable, Consulted, Informed | Matrix of who does, decides, is asked, and is told – here as Decides / Approves / Consulted / Informed. |
| **RBAC / row-level security** | Role-Based Access Control | Permissions by role: which metrics (column / sensitivity level) and which rows (here: region) a role may see. |
| **Restatement** | – | Officially changing numbers of a period that is already closed and reported. Done through a controlled Finance process, never silently by a pipeline. |
| **Retry (duplicate)** | – | A source sends the exact same record again (e.g. after a network timeout). Must be collapsed to one row, never counted twice. |
| **RPO / RTO** | Recovery Point Objective / Recovery Time Objective | RPO = how much data you may lose (e.g. 24 h); RTO = how long recovery may take (e.g. 4 h). |
| **Runbook** | – | Written steps the on-call person follows when an alert fires. |
| **SCD2** | Slowly Changing Dimension, Type 2 | A way to keep history of changing attributes: instead of overwriting, the old row is closed (valid_to) and a new row is opened (valid_from). Used for product category and store region. |
| **Seasonal naive** | – | Forecast = the value of the same week last year. The standard baseline any forecast model must beat. |
| **Seed** | – (dbt term) | A small CSV file kept in the repo and loaded as a table by dbt – used for reference data we own (regions, FX rates, id mappings). |
| **Self-hosted integration runtime (IR)** | – | ADF agent installed inside the client's network so the cloud can read on-prem databases securely. |
| **Semantic versioning (semver)** | – | Version numbers MAJOR.MINOR.PATCH: major = breaking change, minor = additive, patch = fix. |
| **SKU** | Stock Keeping Unit | The unique code for one sellable product variant (e.g. a specific juice in a 1-litre pack). |
| **Snapshot (dbt)** | – | A dbt feature that keeps every past version of a table's rows with `dbt_valid_from` / `dbt_valid_to`. Used for the daily version table `gold.snp_sales_daily`. |
| **SSO / Entra ID** | Single Sign-On / Microsoft Entra ID (formerly Azure AD) | Company login and group membership; in production the user's groups decide their role. |
| **Surrogate key (`_sk`)** | – | A system-generated key for a dimension row (one per version in SCD2), e.g. `product_sk`. Facts link to it, so a sale points to the exact product version valid on the sale date. |
| **Survivorship rule** | – | When two systems hold the same attribute, the rule that decides whose value wins (here: ERP for pack size/status, PIM for brand/category). |
| **Trunk-based development** | – | Short-lived branches merged often into `main`, which is always releasable. |
| **Unity Catalog (UC)** | – | Databricks' governance layer: one catalog of tables, files, models and metric views with permissions, row filters, tags, lineage and audit. |
| **WAPE** | Weighted Absolute Percentage Error | Total absolute forecast error ÷ total actual. 14.5% = on average the forecast is off by 14.5% of actual sales. Weighted, so big series dominate – hence per-series confidence too. |
