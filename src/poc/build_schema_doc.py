"""Generate docs/models/physical_schema.md from dbt's manifest and catalog, so the physical schema
document can never drift from the real tables.   Run: make schema-doc  (runs dbt docs generate first)
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

TARGET = Path("dbt/target")
OUT = Path("docs/models/physical_schema.md")
ORDER = ["ref", "bronze", "silver", "gold"]

HEADER = """# Physical schema

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
"""


def main() -> int:
    manifest = json.loads((TARGET / "manifest.json").read_text())
    catalog = json.loads((TARGET / "catalog.json").read_text())
    tests = defaultdict(lambda: defaultdict(list))   # node_id -> column -> [test names]
    for n in manifest["nodes"].values():
        if n["resource_type"] != "test" or not n.get("attached_node"):
            continue
        name = (n.get("test_metadata") or {}).get("name") or n["name"]
        tests[n["attached_node"]][n.get("column_name") or "(table)"].append(name)

    by_schema = defaultdict(list)
    for uid, n in list(manifest["nodes"].items()):
        if n["resource_type"] in ("model", "seed"):
            by_schema[n["schema"]].append((uid, n))
    lines = [HEADER]
    for schema in ORDER:
        lines.append(f"\n### Schema `{schema}`\n")
        for uid, n in sorted(by_schema[schema], key=lambda x: x[1]["name"]):
            cat = catalog["nodes"].get(uid, {})
            kind = cat.get("metadata", {}).get("type", n["config"].get("materialized", "")).lower()
            mat = n["config"].get("materialized", "")
            contract = " · **contract enforced**" if n["config"].get("contract", {}).get("enforced") else ""
            lines.append(f"#### `{schema}.{n['name']}`  \n*{kind} ({mat}, {n['language'] if 'language' in n else 'sql'})*{contract}\n")
            if n.get("description"):
                lines.append(n["description"].strip().replace("\n", " ") + "\n")
            if tests[uid].get("(table)"):
                lines.append(f"Table tests: {', '.join(sorted(set(tests[uid]['(table)'])))}\n")
            cols = cat.get("columns", {})
            if cols:
                lines.append("| # | Column | Type | Description | Tests |\n|---|---|---|---|---|")
                for c in sorted(cols.values(), key=lambda c: c["index"]):
                    desc = (n.get("columns", {}).get(c["name"], {}).get("description") or "").replace("|", "/")
                    t = ", ".join(sorted(set(tests[uid].get(c["name"], []))))
                    lines.append(f"| {c['index']} | `{c['name']}` | {c['type']} | {desc} | {t} |")
                lines.append("")
    sources = [s for s in manifest["sources"].values()]
    lines.append("\n### Sources (landing files)\n")
    lines.append("| Source | Owner | Location | Description |\n|---|---|---|---|")
    for s in sorted(sources, key=lambda s: s["name"]):
        loc = (s.get("meta", {}).get("external_location") or s["source_meta"].get("external_location", "")).replace("{name}", s["name"])
        lines.append(f"| `landing.{s['name']}` | {s.get('meta', {}).get('owner', '')} | `{loc.split(',')[0]})` | {s['description']} |")
    OUT.write_text("\n".join(lines) + "\n")
    n_tables = sum(len(v) for k, v in by_schema.items() if k in ORDER)
    print(f"Wrote {OUT} - {n_tables} tables/views in {len(ORDER)} schemas, {len(sources)} sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
