.PHONY: up down test lint ingest backfill ensure-bucket model dq

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
