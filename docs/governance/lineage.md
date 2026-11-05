# Lineage approach

Any number must be traceable back to the file that produced it, and every consumer of a table must be
known before it is changed.

## Four levels of lineage

| Level | Question it answers | PoC | Production |
|---|---|---|---|
| **Row → file** | Which delivered file did this sales line come from? | `_source_file` and `batch_id` on every bronze/silver/gold row; `ingested_at` | Same columns + Auto Loader metadata |
| **Table → table** | What feeds this table, what does it feed? | dbt graph from **sources** (landing files) to **exposures** (consumers) – `make docs` | Unity Catalog lineage (automatic) + dbt docs |
| **Column → column** | Which source columns make up `net_sales_inr`? | SQL in the models; physical schema descriptions | UC column-level lineage |
| **Metric / answer → SQL** | How was this number in a report or AI answer calculated? | `make sql` shows compiled SQL; every AI answer carries SQL, parameters, owner, freshness; audit log stores the SQL hash | Metric views + assistant audit table |

## Tracing one number – example

*"South net revenue for FY2026-27 Q2 was ₹1,409,903"* (AI assistant, question A1):

1. **Answer** → audit record: plan, `sql_sha256`, parameters, data as of.
2. **Metric** → `metrics.yml` `net_revenue = sum(f.net_sales_inr)`, owner Finance.
3. **Fact** → `gold.fct_sales_line`, rows with `region_code_at_sale = 'SOUTH'` and dates in the quarter.
4. **Silver** → `slv_sales` (valid, de-duplicated) ← `slv_sales_conformed` (all versions, with `dq_reason`).
5. **Bronze** → `brz_pos_sales` / `brz_ecom_orders` with `_source_file`.
6. **File** → `data/raw/landing/pos/batch=2026-08/pos_sales.csv` (production: UC volume path).

## Rules
- Every new consumer is registered as a **dbt exposure** (owner, type, depends-on) before go-live.
- A change to a model with exposures downstream needs the exposure owners informed (CI/CD notes – contract change management).
- Lineage is generated, never drawn by hand.
