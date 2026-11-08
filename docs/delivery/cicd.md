# CI/CD design notes

## 1. Environments

| Environment | Unity Catalog catalog | Data | Who deploys | Purpose |
|---|---|---|---|---|
| **local / CI** | DuckDB file | Synthetic (this repo) | Anyone / GitHub Actions | Fast feedback on every pull request – exists today |
| **dev** | `cpg_dev` | Sample of real data | Engineers (from branches) | Build and experiment |
| **test** | `cpg_test` | Full real data, masked if required | CI service principal only | Integration, reconciliation, golden set on the real LLM |
| **prod** | `cpg_prod` | Real | CI service principal after approval | Business use |

One Databricks workspace per environment (or one workspace with catalog isolation, decided in [ADR-001](../adr/ADR-001-lakehouse-platform.md)
validation); infrastructure via **Terraform**, jobs and pipelines via **Databricks Asset Bundles**.

## 2. Promotion flow

```
feature branch -> pull request -> CI (today's checks) -> merge to main
      -> deploy bundle to test -> integration gates -> approval -> deploy same bundle (tag) to prod
```

Trunk-based: short-lived branches, every merge releasable; the **same versioned bundle** moves from test
to prod – nothing is rebuilt between environments.

## 3. Gates

| Stage | Gate | Exists in PoC? |
|---|---|---|
| Pull request | `make all`: dbt build (46 data tests + enforced contract), forecast, 65 Python tests incl. AI golden set; Docker build and run, plus the README step-by-step path (dbt docs reachable from the host) | ✅ GitHub Actions |
| Pull request | CODEOWNERS approval for metrics, access policy, contracts, gold, workflows | ✅ `.github/CODEOWNERS` |
| Pull request | dbt **state comparison**: only modified models and their children rebuilt and tested (`state:modified+`) | Prod |
| Test | Full build on real data; **data diff** of gold vs prod (row counts, totals per metric/month) within tolerance | Prod |
| Test | Golden set against the real LLM endpoint; red-team suite for assistant changes | Prod |
| Release | Change approval (platform change process); release notes from commit messages | Prod |
| Post-deploy | Smoke tests: freshness, row counts, one metric per mart vs previous day | Prod |

## 4. Rollback

| What went wrong | Rollback |
|---|---|
| Bad code or config deployed | Redeploy the **previous bundle tag** (jobs, pipelines, dbt project) |
| Bad data written to gold | Delta **`RESTORE TABLE … TO VERSION AS OF`** (time travel kept 30 days); re-run from silver |
| Bad data upstream | Fix, then replay from landing / bronze (append-only) – the pipeline is deterministic (incremental = full refresh) |
| Large gold changes | **Blue/green**: build the new version into a parallel table, validate, then swap the view consumers read |

A rollback drill is part of WS6 acceptance.

## 5. Schema and contract change management

| Change type | Examples | Process |
|---|---|---|
| **Additive** | New optional source column; new gold column; new metric | Minor version; allowed without notice; contract file and docs updated in the same pull request |
| **Breaking** | Rename / remove / retype a column; change a metric's meaning; change grain | **Major version**; 30 days' notice to exposure owners; new version published **alongside** the old one (dbt model versions / `_v2`) for at least one release; old version deprecated then removed |
| **Source-side breaking** | A source renames a field | Contract violation detected (schema-drift signal); bronze keeps raw; mapping updated; source owner reminded of the notice policy |
| **Metric definition** | Revenue starts excluding a channel | Never silently: new metric name or major version; metric owner approval; reconciliation of old vs new published |

Rules: contracts are versioned in git (`contracts/`, `_gold.yml`); dbt's enforced contract fails the
build on an unplanned breaking change; consumers are known through dbt **exposures**.

## 6. Secrets and identities
Service principals per environment; secrets in Azure Key Vault (secret scopes); CI uses **OIDC federation**
to Azure (no stored credentials); no personal access tokens in pipelines.
