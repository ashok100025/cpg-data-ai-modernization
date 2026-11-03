# One-command run path. Works the same locally, in Docker and in CI.
PY      ?= .venv/bin/python
DBT     ?= .venv/bin/dbt
DBTARGS  = --project-dir dbt --profiles-dir dbt

.PHONY: setup data build demo-incremental inspect preview query all clean

setup:            ## create the virtualenv and install pinned dependencies
	python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt

data:             ## land the deterministic synthetic history (Jan 2025 - Sep 2026)
	rm -rf data/raw/landing && $(PY) src/poc/generate_data.py

build:            ## bronze -> silver -> gold, with all data tests
	mkdir -p data/warehouse && $(DBT) build --full-refresh $(DBTARGS)

demo-incremental: ## land the October batch (late data, corrections, bad rows) and run incrementally
	$(PY) src/poc/generate_data.py --demo-batch && $(DBT) build $(DBTARGS)

inspect:          ## show every schema/table with row counts, reconciliation, quarantine by reason
	$(PY) src/poc/inspect_warehouse.py

ROWS ?= 20
preview:          ## first rows of one table: make preview TABLE=gold.dim_store [ROWS=20]
	@test -n "$(TABLE)" || (echo 'usage: make preview TABLE=gold.dim_store [ROWS=20]'; exit 1)
	@$(PY) src/poc/inspect_warehouse.py --preview "$(TABLE)" --rows $(ROWS)

query:            ## any read-only SQL: make query SQL="select ..."
	@test -n "$(SQL)" || (echo 'usage: make query SQL="select ... from gold.fct_sales_line"'; exit 1)
	@$(PY) src/poc/inspect_warehouse.py --sql "$(SQL)" --rows $(ROWS)

all: data build

clean:
	rm -rf data/raw/landing data/warehouse dbt/target dbt/logs
