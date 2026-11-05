# Assumptions register

Every assumption the design and PoC rely on, who must confirm it, what breaks if it is wrong, and how
to validate it. IDs are referenced in code comments, contracts, metric definitions and ADRs.

**Status:** *Assumed* = used in the PoC, not yet confirmed. *Open question* = needs a decision before
production. Nothing here is confirmed yet – confirming them is the first task of discovery (Phase 0).

| ID | Assumption | Used in | Confirm with | If wrong | How to validate | Status |
|---|---|---|---|---|---|---|
| A-01 | **Net revenue** = gross sales − returns; **tax excluded**; discounts already netted in the paid price | `metrics.yml` `net_revenue`, `fct_sales_line` | Finance (CFO office) | Every revenue number is wrong by the tax/discount effect | Reconcile one closed month against the finance ledger | Assumed |
| A-02 | Region reporting is **as-was** by default (a sale stays with the region at sale time); as-is available | `fct_sales_line.region_code_at_sale`, dimension `region` | Sales Operations | Regional performance and bonuses computed on the wrong basis | Walk Sales Ops through the S003 example; agree default per report | Assumed |
| A-03 | **Survivorship:** ERP owns identity, pack size, launch date, lifecycle status; PIM owns brand and category; ERP wins on shared attributes | `slv_product_history`, `slv_product_conflicts` | Master Data owner | Wrong attributes on products; conflicts resolved the wrong way | Review the conflict queue (`slv_product_conflicts`) with Master Data | Assumed |
| A-04 | **Fiscal calendar:** year starts on the Monday of the week containing 1 April; 13-week quarters split **4-4-5**; week 53 folds into P12 | `dim_date` | Finance | Period reports and year-on-year comparisons misaligned | Compare `dim_date` with Finance's published calendar | Assumed |
| A-05 | **Late data window:** lines accepted up to **14 days** after the batch period starts; later lines/corrections go to a Finance **restatement** queue | `late_window_days`, `LATE_BEYOND_WINDOW` (ADR-004) | Finance + Data Platform | Either closed periods change silently, or valid late sales wait too long | Agree close calendar; measure real lateness distribution per source in Phase 1 | Assumed |
| A-06 | **FX:** non-INR sales converted at the **monthly average** rate to INR | `fx_rates_monthly`, `fct_sales_line` | Finance / Treasury | UAE revenue mis-stated by daily FX movement | Compare with Treasury's rate source and policy | Assumed |
| A-07 | **E-commerce attribution:** an online order belongs to the store of its fulfilment node | `fulfilment_node_xref` | Sales Ops + Digital Commerce | Store/region revenue shifts between channels | Agree attribution rule; check against current e-com reporting | Assumed |
| A-08 | **Effective dates** of product/store changes = the monthly **extract date** (sources do not send effective-from) | `dim_product`, `dim_store` (ADR-002) | Master Data, Sales Ops | History boundaries up to a month off | Ask source owners for effective-from fields; adopt them if available | Assumed |
| A-09 | **Batch cadence:** monthly batches in the PoC; production daily (POS/e-com) and monthly (masters) | landing layout, `source_contracts.yml` | Data Platform + source owners | Freshness SLAs mis-designed | Confirm feed schedules with each source owner | Assumed |
| A-10 | **Demand** = net units sold (**observed** demand); stock-outs invisible until inventory is ingested | `metrics.yml` `net_units`, forecast | Supply Chain / Demand Planning | Forecast under-states true demand where stock-outs occur | Onboard inventory (optional signal) and compare | Assumed |
| A-11 | **Reporting currency INR**; India + UAE stores; 12 stores, 40 SKUs in the PoC (synthetic) | all amounts | Finance | Currency of record wrong for group reporting | Confirm group reporting currency | Assumed |
| A-12 | **Forecast uses as-is** region/category; reporting stays as-was | forecast (D10) | Demand Planning + Sales Ops | Forecasts not comparable with how plans are set | Agree planning hierarchy | Assumed |
| A-13 | **Recovery targets** (proposed): curated data RPO 24 h / RTO 4 h; reporting RTO 4 h; AI assistant best effort | architecture NFRs | Business owners + Platform team | DR over- or under-engineered | Business impact analysis per consumer | Open question |
| A-14 | **Azure Central India** primary region; **UAE data residency** not yet assessed | architecture | Legal / Compliance + Security | UAE sales may need to stay in-country | Legal review of UAE data rules before Phase 1 | Open question |
| A-15 | **Identity:** roles come from SSO (Entra ID) groups mapped to Unity Catalog groups; the PoC passes the role as an argument | `access_policy.yml` | Security / IAM | Access policy cannot be enforced as designed | Map real groups in Phase 0 | Assumed |
| A-16 | **Commercially sensitive** = pricing and promotion economics (`avg_selling_price`, `promo_*`); everything else internal | `metrics.yml` sensitivity | Commercial director + Data Governance | Over- or under-restricted access | Classification workshop | Assumed |
| A-17 | No **customer personal data** is in scope; PII would need a separate design | access model | Data Protection Officer | Privacy controls missing | Confirm no loyalty/customer feeds in scope | Assumed |
| A-18 | **Migration phase durations** are indicative (P0 ~4 wks, P1 ~8–10, P2 ~8, P3 ~8–12) | architecture | Programme sponsor | Plan and budget wrong | Re-estimate after discovery | Open question |

## Requirements to confirm with stakeholders (from the brief: *"identify which requirements you would confirm"*)

| Stakeholder | Questions to settle first |
|---|---|
| **Finance** | A-01 revenue definition, A-04 fiscal calendar, A-05 close and restatement process, A-06 FX policy, A-11 currency |
| **Sales Operations** | A-02 as-was default, A-07 e-com attribution, A-08 effective dates of store moves |
| **Master Data** | A-03 survivorship rules, A-08 effective dates, owner of the conflict queue |
| **Supply Chain / Planning** | A-10 demand definition, A-12 planning hierarchy, forecast grain and horizon |
| **Commercial / Data Governance** | A-16 sensitivity classification, who may see pricing and promotion economics |
| **Platform / Security** | A-09 feed schedules, A-13 RPO/RTO, A-14 region and residency, A-15 identity mapping, A-17 PII scope |
