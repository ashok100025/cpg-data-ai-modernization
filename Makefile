# One-command run path. Works the same locally, in Docker and in CI.
PY      ?= .venv/bin/python
DBT     ?= .venv/bin/dbt
DBTARGS  = --project-dir dbt --profiles-dir dbt

.PHONY: setup data build forecast test demo-incremental inspect preview query sql ask ai-demo docs docs-generate docker-build docker-run all clean

setup:            ## create the virtualenv and install pinned dependencies
	python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt

data:             ## land the deterministic synthetic history (Jan 2025 - Sep 2026)
	rm -rf data/raw/landing && $(PY) src/poc/generate_data.py

build:            ## bronze -> silver -> gold, with all data tests
	mkdir -p data/warehouse && $(DBT) build --full-refresh $(DBTARGS)

forecast:         ## backtest + 8-week forecast of net revenue and net units -> gold.forecast_*
	$(PY) src/poc/forecast.py

test:             ## Python tests: metric compiler, forecast models, leakage guards
	$(PY) -m pytest -q tests

demo-incremental: ## land the October batch (late data, corrections, bad rows), run incrementally, re-forecast
	$(PY) src/poc/generate_data.py --demo-batch && $(DBT) build $(DBTARGS) && $(PY) src/poc/forecast.py

inspect:          ## show every schema/table with row counts, reconciliation, quarantine by reason
	$(PY) src/poc/inspect_warehouse.py

ROWS ?= 20
preview:          ## first rows of one table: make preview TABLE=gold.dim_store [ROWS=20]
	@test -n "$(TABLE)" || (echo 'usage: make preview TABLE=gold.dim_store [ROWS=20]'; exit 1)
	@$(PY) src/poc/inspect_warehouse.py --preview "$(TABLE)" --rows $(ROWS)

query:            ## any read-only SQL: make query SQL="select ..."
	@test -n "$(SQL)" || (echo 'usage: make query SQL="select ... from gold.fct_sales_line"'; exit 1)
	@$(PY) src/poc/inspect_warehouse.py --sql "$(SQL)" --rows $(ROWS)

sql:              ## SQL the metric compiler generates: make sql METRICS=net_revenue,return_rate BY=region,week
	@test -n "$(METRICS)" || (echo 'usage: make sql METRICS=net_revenue,return_rate [BY=region,week] [WHERE="region=SOUTH"]'; exit 1)
	@$(PY) -m src.poc.metrics --metrics "$(METRICS)" --by "$(BY)" $(if $(WHERE),--where "$(WHERE)")

ROLE ?= finance_analyst
ask:              ## governed AI assistant: make ask Q="net revenue by region last quarter" [ROLE=regional_manager_south]
	@test -n "$(Q)" || (echo 'usage: make ask Q="What was net revenue by region last quarter?" [ROLE=finance_analyst]'; exit 1)
	@$(PY) -m src.poc.insight.cli --role "$(ROLE)" "$(Q)"

ai-demo:          ## scripted demo: answered, restricted, refused (unauthorized / unsupported / injection)
	@$(PY) -m src.poc.insight.cli --demo

docs-generate:    ## dbt documentation site incl. lineage graph -> dbt/target/index.html
	$(DBT) docs generate $(DBTARGS)

docs: docs-generate ## generate and open the dbt docs site on http://localhost:8080
	$(DBT) docs serve $(DBTARGS) --port 8080

docker-build:     ## build the container image (needs Docker)
	docker build -t cpg-data-ai-poc .

docker-run:       ## run the whole PoC inside the container
	docker run --rm cpg-data-ai-poc

all: data build forecast test

clean:
	rm -rf data/raw/landing data/warehouse dbt/target dbt/logs
