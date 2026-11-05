# Access model

Who may see what, how it is enforced in the PoC, and how it maps to Unity Catalog in production.

## 1. Data classification

| Level | Meaning | Examples | Default access |
|---|---|---|---|
| `internal` | Business data for employees with a need | net revenue, units, return rate | Analysts, managers (within row scope) |
| `commercially_sensitive` | Would harm the company if leaked to competitors or retailers (A-16) | `avg_selling_price`, `promo_revenue`, `promo_revenue_share` | Finance, Commercial leadership |
| `restricted` (reserved) | Personal or regulated data | none in scope (A-17) | Separate design required |

Labels live on each metric in `metrics/metrics.yml`; in production they become **Unity Catalog tags**.

## 2. Roles

| Role | Regions (row scope) | Max sensitivity | Typical users | Production identity |
|---|---|---|---|---|
| `finance_analyst` | all | commercially_sensitive | Finance, FP&A | Entra ID group → UC group `grp_finance_analyst` |
| `sales_analyst` | all | internal | Commercial analytics | `grp_sales_analyst` |
| `regional_manager_<region>` | own region only | internal | Regional managers | `grp_rm_south` etc. (from `dim_region.region_manager_role`) |
| *unknown role* | – | – | – | **denied by default** |
| `data_engineer` | all (bronze/silver write in dev/test) | n/a – no consumer access in prod | Pod engineers | `grp_data_engineers` |
| `pipeline_sp` | write bronze → gold in prod | n/a | Service principal | Jobs and CI only |

## 3. Enforcement – PoC vs production

| Control | PoC (`policies/access_policy.yml`, `src/poc/insight/policy.py`) | Production (Unity Catalog) |
|---|---|---|
| Metric sensitivity | Assistant refuses metrics above the role's level | Grants on **metric views** per sensitivity; tags + ABAC policies |
| Row scope | Region filter **forced** into the compiled query | **Row filter** function on gold tables / metric views |
| Layer access | – | Consumers: `SELECT` on gold and metric views only; engineers: bronze/silver in dev/test; only `pipeline_sp` writes prod |
| Unknown identity | Denied | No grant = no access |
| Audit | `outputs/audit/insight_audit.jsonl` | UC audit / system tables + assistant audit table |

Example production row filter (illustrative):

```sql
create function gold.region_filter(region_code string)
return is_account_group_member('grp_finance_analyst')
    or is_account_group_member('grp_sales_analyst')
    or (region_code = 'SOUTH' and is_account_group_member('grp_rm_south'));

alter table gold.fct_sales_line set row filter gold.region_filter on (region_code_at_sale);
```

## 4. AI access path
The assistant runs **as the asking user's role** – it never has broader access than the user. The LLM
receives the question and catalogue metadata only, **never rows**; SQL comes from the compiler; the
row scope is forced after planning. See ADR-003.

## 5. Operating the model
- **Access requests** through group membership (IAM process), never direct grants to people.
- **Quarterly access review** of group memberships by Data Governance.
- **Break-glass** admin account, monitored and alerted on use.
- **Policy changes** (`access_policy.yml` / UC grants) by pull request, approved by Data Governance (`.github/CODEOWNERS`), proven by the golden set in CI.
