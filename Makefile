.PHONY: up down test lint ingest backfill ensure-bucket model dq migrate api load cdc apply e2e tf-check dbt-deps dbt-build dbt-docs

DBT_PROJECT := transform/dbt
DBT := $(PY) -m transform.dbt_main --project-dir $(DBT_PROJECT) --profiles-dir $(DBT_PROJECT)

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
	$(DBT) deps

dbt-build:
	$(DBT) build

dbt-docs:
	$(DBT) docs generate

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
