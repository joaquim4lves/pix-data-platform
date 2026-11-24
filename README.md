# pix-data-platform

Senior backend engineer and tech lead with 10+ years shipping production APIs in Python and Node. This repository is an end-to-end data platform I designed and built: public PIX payments data from Banco Central do Brasil lands in S3, is transformed and tested in dbt, orchestrated in Airflow, and explored in Metabase, with AWS infrastructure in Terraform. It applies production habits (idempotent ingestion, data tests, retries, freshness checks, infrastructure as code) to an analytical stack in the payments domain.

v0.1 is the ingestion slice: public PIX statistics from the BCB Olinda API land as Parquet partitions on S3. LocalStack stands in for S3 so the slice runs without an AWS account. v0.2 models that raw zone as a star schema in DuckDB. v0.3 adds a simulated PSP on Postgres and captures its changes with logical replication. v0.4 is the low-cost AWS account (S3, Lambda, SQS, Glue, Athena). Postgres, Airflow, and Metabase stay on the laptop. Later releases add dbt and the Airflow DAGs.

```mermaid
flowchart LR
  subgraph source [Source]
    Olinda["BCB Olinda Pix_DadosAbertos"]
  end
  subgraph ingest [v0.1 ingestion]
    Client["Olinda client<br/>retry, filter, page"]
    Contract["Pydantic contract"]
    Writer["Parquet writer"]
  end
  subgraph local [Local stand-in for AWS]
    Raw["s3://bucket/raw/bcb/entity/ano_mes=YYYYMM/"]
    State["watermark state"]
    Quarantine["s3://bucket/quarantine/"]
  end
  Olinda --> Client --> Contract --> Writer --> Raw
  Writer --> State
  Contract -->|invalid payload| Quarantine
```

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env   # optional; the defaults match this compose file
make up && make ingest && make test
```

`make up` starts Postgres 16 (with `wal_level=logical`) and LocalStack S3 and SQS, waits until both are healthy, and creates the raw bucket. `make ingest` pulls the last three months from the live BCB API and overwrites those partitions. `make test` runs the unit suite and, when LocalStack is up, the S3 integration tests. The API tests run when Postgres answers on port 5432; CI starts a Postgres service for them. The logical-replication test runs only when `wal_level` is `logical`, so it skips in CI. The DuckDB model tests use fixture Parquet and do not need the network.

Other targets:

```bash
make lint
make down
make backfill START=202011 END=202012
python -m ingestion.bcb ingest --entities ChavesPix --lookback-months 3
PIX_RAW_SOURCE=s3 make model && make dq
```

The Lambda-style entrypoint is `ingestion.bcb.handler.handler`. It reads the same environment variables and accepts `{"mode": "ingest"}` or `{"mode": "backfill", "start": 202011, "end": 202012}`.

## v0.1 scope

In this release:

- Python 3.12 project (`pyproject.toml`), Makefile, GitHub Actions (ruff + pytest), `.gitignore`, `.env.example`
- `docker-compose.yml` with Postgres and LocalStack S3
- Olinda client with retries, backoff, `$filter`, and `$top`/`$skip` pagination
- Pydantic contracts and a PyArrow Parquet writer for `EstatisticasTransacoesPix`, `TransacoesPixPorMunicipio`, and `ChavesPix`
- Incremental watermark in `s3://<bucket>/raw/bcb/_state/watermarks.json`, reprocessing the last N months (default 3) by overwriting whole partitions
- Backfill with `--start` and `--end`
- Quarantine of a payload that breaks the contract, under `s3://<bucket>/quarantine/<entity>/`
- Unit tests for the client, the watermark, and partition overwrite, plus a LocalStack integration test that skips when the endpoint is down

Not in v0.1: the warehouse, the payments app, CDC, Terraform, real AWS, dbt, Airflow, Metabase. The star schema is v0.2. The payments app and CDC are v0.3. Postgres is running so that slice has a database; ingestion does not connect to it.

The API behaves differently from a plain OData month parameter. Read [docs/spike-bcb.md](docs/spike-bcb.md) before changing the client. The local-first choice is recorded in [docs/adr/ADR-001.md](docs/adr/ADR-001.md).

## v0.2 scope

`make model` builds a local DuckDB file (`data/pix.duckdb`) from the raw Parquet. `make dq` runs the data-quality checks against that file. The default source is a local directory, `data/raw`, laid out like the bucket (`bcb/<entity>/ano_mes=YYYYMM/part.parquet`). After `make ingest` the files are in LocalStack, so point the build at S3:

```bash
PIX_RAW_SOURCE=s3 make model
make dq
```

DuckDB reads that bucket through httpfs. The first S3 build downloads the extension. An empty `AWS_ENDPOINT_URL` is real S3 and uses virtual-hosted addressing; a set endpoint (LocalStack) uses path-style HTTP. The same switch as the ingestion client.

The models are plain SQL, one file each, under `transform/sql/` in four layers: seeds, staging, intermediate, and marts. Staging renames and types the Olinda columns. Intermediate keeps the monthly `N/D` municipality as `Não informado` (`municipio_ibge` 0) and derives the key-snapshot month. Marts are the star schema. Facts:

- `fct_transacoes_mensal`: one row per month and the published combination of person type, region, age band, initiation form, natureza, and finalidade. `valor` and `quantidade` add to the national month.
- `fct_transacoes_municipio`: one row per month and municipality, including `Não informado`. Value sent and value received are separate. Do not add them.
- `fct_chaves_pix`: one row per snapshot month, ISPB, person type, and key type. A stock of keys, not payment volume.

`dim_natureza` maps the nine raw codes and records where each label comes from. A code that is not in the seed is kept. Fraud is not modeled: it is not in the raw zone. Example questions (volume by month, top UFs and municipalities by value received, key-type mix) are in [docs/queries](docs/queries). There is no population in the extract, so those rankings are not per capita. The grain and the DuckDB choice are recorded in [docs/adr/ADR-002.md](docs/adr/ADR-002.md).

Tests build a small Parquet fixture with the ingestion writer and run the models and the checks locally. CI does not call Olinda or S3 for this slice. The LocalStack httpfs test skips when port 4566 is closed, same as the ingestion integration test.

## v0.3 scope

A simulated payment institution lives in the compose Postgres: a PIX key registry, the payments that institution sends and receives, and a small MED-style dispute table. `ispb` is 8 digits, `municipio_ibge` is the IBGE municipality code, and key types and initiation forms use the same literals as the v0.2 dimensions, so the operational rows can be joined to them.

```mermaid
flowchart LR
  Api["FastAPI payments"] --> Pg["Postgres logical WAL"]
  Pg --> Slot["pgoutput slot"]
  Slot --> Sqs["SQS pix-cdc"]
  Sqs --> Sink["Parquet sink"]
  Sink --> Raw["s3 raw/app/table/dt="]
  Raw --> Cur["DuckDB cur_* current state"]
```

`make api` applies the Alembic migrations and serves the API on port 8000 (`/health`, `/docs`, CRUD under `/keys`, `/transactions`, and `/disputes`). `make load` writes inserts, then updates, then deletes, one commit each. `make cdc` reads the `pgoutput` slot and publishes a JSON envelope (`op`, `table`, `pk`, `before`, `after`, `lsn`, `commit_ts`) to SQS. `make apply` writes those messages as Parquet at `raw/app/<table>/dt=YYYY-MM-DD/` and skips a repeat of the same commit LSN and primary key. `make model` builds `cur_pix_key`, `cur_pix_transaction`, and `cur_pix_dispute`: the latest image per id, with deletes removed.

A replication slot does not see rows that were committed before it existed. Start `make cdc` before `make load`, or use `make e2e`, which recreates the slot, resets the tables, loads, drains the queue, and checks the current-state tables against Postgres. `make e2e` needs `make up` first. Debezium is not in this slice. The tradeoff, the at-least-once path, and the WAL retention risk are in [docs/adr/ADR-003.md](docs/adr/ADR-003.md).

```bash
make up
make e2e
```

## v0.4 scope

Real S3 replaces LocalStack when `AWS_ENDPOINT_URL` is empty or `aws`. The account is the low-cost shape in [ADR-004](docs/adr/ADR-004.md): S3, two Lambdas, SQS, Glue partition projection, Athena, a USD 5 budget, and a GitHub OIDC deploy role. There is no EC2 instance, RDS database, load balancer, or NAT gateway. Postgres, the pgoutput consumer, Airflow, and Metabase stay on the laptop. Metabase is not installed here; the dotted SQL edge is the path a local Metabase uses to read Athena.

```mermaid
---
title: Infrastructure v2 — local Docker and a low-cost AWS account
config:
  theme: neutral
  layout: elk
  flowchart:
    rankSpacing: 28
    nodeSpacing: 24
    htmlLabels: true
    curve: basis
  themeVariables:
    lineColor: "#555555"
    primaryTextColor: "#1a1a1a"
---
flowchart TB
  bcb["BCB Olinda API — external"]
  gh["GitHub — external"]
  bcb ~~~ gh

  subgraph local["Local — Docker on the dev machine"]
    direction TB
    pg[("PostgreSQL")]
    cdc["Python pgoutput consumer"]
    af["Airflow — local only"]
    mb["Metabase — queries Athena"]
    pg --> cdc
    cdc ~~~ af
    af ~~~ mb
  end

  subgraph aws["AWS account"]
    direction TB
    ev["EventBridge Scheduler"]
    lam["Lambda — BCB ingest"]
    s3b["S3 Parquet — raw/bcb/ENTITY/ano_mes=YYYYMM"]
    ev -->|"schedule"| lam
    lam --> s3b

    sqs["SQS + DLQ"]
    sink["Lambda — CDC sink"]
    s3a["S3 Parquet — raw/app/TABLE/dt="]
    sqs --> sink --> s3a

    glue["Glue Data Catalog — partition projection, no crawlers"]
    ath["Athena workgroup — bytes-scanned limit"]
    s3b --> glue
    s3a --> glue
    glue --> ath

    bud["AWS Budgets, USD 5 / month"]
    cw["CloudWatch Logs"]
    iam["IAM — least privilege"]
    tf["Terraform remote state — S3"]
    bud ~~~ cw
    cw ~~~ iam
    iam ~~~ tf
  end

  bcb -->|"HTTPS pull"| lam
  cdc --> sqs
  gh -->|"Actions via OIDC"| iam
  mb -.->|"SQL"| ath
```

The dev root is `infra/terraform/envs/dev`. CI runs `terraform fmt`, `init -backend=false`, `validate`, tflint, and checkov. It does not apply. A manual workflow runs plan or apply only when the deploy role, state bucket, region, and budget email are set. Steps are in [docs/runbooks/aws-dev.md](docs/runbooks/aws-dev.md). The cost estimate is [docs/cost-estimate.md](docs/cost-estimate.md).

In this release:

- Data lake bucket with `raw/`, `curated/`, and `athena-results/`, SSE-S3, public access blocked, and lifecycle rules
- BCB ingest Lambda packaged from `ingestion/`, scheduled daily and monthly in `America/Sao_Paulo`
- SQS queue, dead-letter queue, and CDC sink Lambda. The event source mapping uses `ReportBatchItemFailures`
- Glue databases and external tables with partition projection, and no crawlers
- Athena workgroup with an enforced 1 GiB bytes-scanned cutoff
- Account-wide budget of USD 5. The inbox is `budget_alert_email`
- 14-day CloudWatch log retention and least-privilege IAM
- GitHub Actions OIDC provider and a deploy role scoped to this repository's deploy workflow
- Remote state in S3 with Terraform's native lockfile, plus a bootstrap root
- `transform/athena/views.sql`, Athena views generated from the DuckDB models

The default region is `us-east-1` because that is where the unit prices and the free tier are cheapest. `aws_region = "sa-east-1"` keeps the buckets in São Paulo. A quiet month should cost about zero dollars. Read the cost table before leaving a stack applied.

## Ingestion behavior

A run asks Olinda for each month in the window with `$filter`, validates every row, and writes one Parquet file per month:

`s3://<bucket>/raw/bcb/<entity>/ano_mes=YYYYMM/part.parquet`

The write deletes whatever is already under that prefix, so a second run replaces the partition. The same rows produce the same table. An empty response does not delete an existing partition: several series publish late, and an empty body must not wipe a good month.

The watermark is the newest **closed** month written for that entity. The calendar is America/Sao_Paulo. The current month is fetched when it falls inside the lookback window, and it is not stored as the watermark, because `TransacoesPixPorMunicipio` already contains the month before it closes. A watermark older than the window is caught up, including a revision of the previous N months. History before that window is a backfill, not a side effect of `make ingest`.

`NATUREZA`, `FORMAINICIACAO`, and the other classifications are stored as Olinda sent them. The loader does not invent display names.

If a row breaks the contract, that entity stops, the raw response is written to quarantine, the watermark stays where it was, and the other entities still run. The process exits non-zero.

## Roadmap

| Release | What lands |
| --- | --- |
| v0.1 | Foundation and incremental BCB PIX ingestion |
| v0.2 | Star schema in DuckDB over the raw Parquet |
| v0.3 | FastAPI + Postgres payments app, CDC via `pgoutput` |
| v0.4 | This slice: low-cost serverless AWS. Postgres and Airflow stay in Docker |
| v0.5 | dbt models and tests |
| v0.6 | Airflow orchestration |
| v1.0 | Metabase and the final README |

## Layout

```text
ingestion/bcb/                 client, contracts, watermark, Parquet writer, CLI, handler
payments/                      FastAPI app, SQLAlchemy models, Alembic, load generator
cdc/                           pgoutput decoder, SQS publisher, Parquet sink, Lambda handler
transform/sql/staging/         typed Olinda columns and the CDC log
transform/sql/intermediate/    N/D municipality, snapshot month, ISPB padding
transform/sql/seeds/           natureza labels, IBGE UFs, other code lists
transform/sql/marts/           dimensions and facts
transform/sql/checks/          data-quality queries (one row per violation)
docs/queries/                  example analytical questions
docs/spike-bcb.md              what the live Olinda service actually does
docs/adr/                      architecture decisions, including ADR-004
docs/architecture/             infrastructure diagram
docs/runbooks/                 deploy and destroy
docs/cost-estimate.md          expected AWS bill
docs/career/                   positioning kit, not part of the pipeline
infra/terraform/               modules, bootstrap, and envs/dev
transform/athena/views.sql     Athena views generated from the models
tests/                         unit tests, fixture Parquet, LocalStack integration
```
