.PHONY: up down test lint ingest backfill ensure-bucket model dq migrate api load cdc apply e2e tf-check dbt-deps dbt-build dbt-docs airflow-up airflow-down airflow-test metabase-up metabase-down metabase-provision metabase-validate

AIRFLOW_SERVICES := airflow-apiserver airflow-scheduler airflow-dag-processor

DBT_PROJECT := transform/dbt
# Flags follow the subcommand. dbt 1.12 accepts --project-dir there.
DBT := $(PY) -m transform.dbt_main
DBT_FLAGS := --project-dir $(DBT_PROJECT) --profiles-dir $(DBT_PROJECT)

PYTHON ?= python3
VENV := .venv
PY := $(PYTHON)
ifneq ($(wildcard $(VENV)/bin/python),)
PY := $(VENV)/bin/python
endif

ifneq ($(wildcard .env),)
include .env
export
endif

up:
	docker compose up -d --wait
	$(PY) -m ingestion.bcb ensure-bucket

down:
	docker compose down --remove-orphans

test:
	$(PY) -m pytest

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

ingest:
	$(PY) -m ingestion.bcb ingest

backfill:
	@test -n "$(START)" && test -n "$(END)" || (echo "usage: make backfill START=YYYYMM END=YYYYMM" && exit 1)
	$(PY) -m ingestion.bcb backfill --start $(START) --end $(END)

ensure-bucket:
	$(PY) -m ingestion.bcb ensure-bucket

model:
	$(PY) -m transform build

dq:
	$(PY) -m transform dq

dbt-deps:
	$(DBT) deps $(DBT_FLAGS)

dbt-build:
	$(DBT) build $(DBT_FLAGS)

dbt-docs:
	$(DBT) docs generate $(DBT_FLAGS)

airflow-up:
	docker compose --profile airflow up -d --build --wait airflow-apiserver airflow-scheduler airflow-dag-processor

airflow-down:
	docker compose stop $(AIRFLOW_SERVICES)
	docker compose rm -f $(AIRFLOW_SERVICES) airflow-init

airflow-test:
	$(PY) -c "import airflow, cosmos"
	$(PY) -m pytest tests/test_orchestration.py tests/test_airflow_dags.py

migrate:
	$(PY) -m payments migrate

api:
	$(PY) -m payments serve

load:
	$(PY) -m payments load

cdc:
	$(PY) -m cdc consume

apply:
	$(PY) -m cdc apply

e2e:
	$(PY) -m cdc e2e

tf-check:
	terraform fmt -check -recursive -diff infra/terraform
	terraform -chdir=infra/terraform/bootstrap init -backend=false -input=false
	terraform -chdir=infra/terraform/bootstrap validate
	terraform -chdir=infra/terraform/envs/dev init -backend=false -input=false
	terraform -chdir=infra/terraform/envs/dev validate

metabase-up:
	mkdir -p data/metabase
	chmod 777 data data/metabase
	docker compose --profile metabase up -d --wait metabase

metabase-down:
	docker compose --profile metabase stop metabase

metabase-provision:
	PIX_AS_OF_DATE=$${PIX_AS_OF_DATE:-2026-11-25} $(PY) -m dashboards.provision

metabase-validate:
	$(PY) -m dashboards.validate
