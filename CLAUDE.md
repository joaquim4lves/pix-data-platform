# pix-data-platform

Public portfolio of PIX open data from Banco Central do Brasil. Olinda `Pix_DadosAbertos` v1 lands as Parquet, dbt models it on DuckDB, and Metabase serves three dashboards. Airflow 3.4 and a pgoutput CDC path run in Docker. Terraform describes a small AWS account and has not been applied. v1.0 figures for MED, CNAE, and DICT users come from a seeded extract, not a live download. ADR index: @docs/adr/README.md

## Repo map

- `ingestion/bcb/` Olinda client, contracts, Parquet writer, watermarks
- `transform/dbt/` dbt project, the transformation source of truth
- `transform/sql/` and `transform/athena/views.sql` are parity oracles, not where new models go
- `transform/dbt_raw.py` binds each raw Parquet glob to a DuckDB variable
- `orchestration/` Airflow DAGs (`orchestration/dags`) and Cosmos
- `dashboards/` Metabase collection, SQL, and the provisioner
- `payments/`, `cdc/` FastAPI, Postgres, pgoutput
- `infra/terraform/` AWS design. CI validates it. It has not been applied
- `docs/runbooks/`, `docs/spike-bcb.md`, `docs/agentic/`

## Commands

These targets exist in the Makefile. Do not invent others.

Setup: `python3 -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'`. DAG import tests need `pip install -e '.[dev,airflow]'`.

- `make up` / `make down` start local Docker and ensure the bucket
- `make ingest` loads the three live entities. History is `make backfill START=YYYYMM END=YYYYMM`
- `make dbt-deps` then `make dbt-build` run seeds, models, and tests. There is no separate dbt test target
- `make dbt-docs` generates the docs site. `make model` and `make dq` are the legacy SQL runner
- `make airflow-up` / `make airflow-down` / `make airflow-test`
- `make metabase-up` / `make metabase-provision` / `make metabase-validate` / `make metabase-down`
- `make lint` is `ruff check .` and `ruff format --check .`
- `make test` is pytest
- `make tf-check` is `terraform fmt -check`, `init -backend=false`, and `validate`. It does not plan or apply

CI writes fixture Parquet before dbt:

`python -c "from pathlib import Path; from tests.pix_warehouse import write_sample_raw; write_sample_raw(Path('data/raw'))"`

sqlfluff is not installed here. Do not add it in passing.

## Style

Python 3.12. Ruff line length 100, select E, F, I, UP, B. Staging SQL quotes an Olinda name once, then uses snake_case. Measures stay `decimal(38, 8)`. On DuckDB, staging and intermediate are views and marts are tables. An architectural change gets the next file in `docs/adr/`. Do not relitigate an accepted ADR inside a slice.

## Data domain

- Call function imports, not the underscore entity sets. The path argument is a lower bound, so every read sends `$filter` for that `AnoMes`. `$skip` returns HTTP 500. `$count` returns HTTP 403. The grain is monthly.
- `NATUREZA` has nine codes: B2B, B2G, B2P, G2B, G2G, G2P, P2B, P2G, P2P. Store the raw code.
- Each municipality month includes one `N/D` row with a null IBGE code. Keep the row. The mart label is `Unstated / other (N/D)`.
- Do not treat the in-progress America/Sao_Paulo month as closed. The watermark moves only to a closed month this run wrote.
- Transaction and municipality figures are SPI-settled. They are not a ranking of participants. Key stock is not payment volume. The MED-to-SPI ratio uses an SPI-only denominator and is not an official BCB rate.
- MED is national and published about 30 days after month-end. A missing month is a sentence, not a zero. Say "contested via MED". Never say "fraud" for those counts.
- `make ingest` loads `EstatisticasTransacoesPix`, `TransacoesPixPorMunicipio`, and `ChavesPix`. MED, CNAE, and DICT users are contracted and seeded. They are not on `ENTITY_ORDER`.

## Hard rules

- Never run `terraform apply` or `terraform destroy`. Never call a mutating AWS API. `make tf-check` is the ceiling.
- Never commit secrets or `.env`. `.env.example` is the template. The Metabase password in the README is a local demo credential.
- Never edit or delete a test to make it pass. Keep `make dbt-build` green.
- One slice per PR. Explore, plan, code, verify, then commit. Use `/verify`.

## Where to read next

Runbooks and the Olinda spike are long. Open the file the task needs: `docs/runbooks/metabase-local.md`, `docs/runbooks/airflow-local.md`, `docs/runbooks/aws-dev.md`, `docs/spike-bcb.md`. Agent workflow: `docs/agentic/README.md`. Ledger: `docs/agentic/feature_list.json`. Change `passes` only after the steps pass. Do not delete a feature.
