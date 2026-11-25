# Metabase on the laptop

Metabase reads the dbt marts in DuckDB. It does not query Athena. Nothing in this runbook applies Terraform or spends AWS money.

The image and the driver pin are in [ADR-007](../adr/ADR-007.md): `ghcr.io/motherduckdb/metabase-duckdb:0.63.17-duckdb1.5.6.0` (Metabase 0.63.17, MotherDuck DuckDB driver 1.5.6.0). The official Alpine image cannot load the driver.

## First run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
make metabase-up
make metabase-provision
```

`make metabase-up` starts the `metabase` compose profile and waits until `/api/health` is ok. `make metabase-provision` writes a seeded extract under `data/demo-raw`, builds `data/pix.duckdb` as of 2026-11-25, and creates the collection **PIX Open Data** from `dashboards/metabase/`.

Open http://localhost:3000.

| Field | Value |
| --- | --- |
| Email | `pix@example.com` |
| Password | `PixLocal-1a` |

Those credentials exist only for this local instance. The H2 application database is `data/metabase/`. The warehouse file is `data/pix.duckdb`. Both are gitignored.

The three dashboards:

1. **PIX at a glance** — national SPI totals, natureza, initiation mix, DICT users and key stock.
2. **Where it moves** — region, state and municipality. Receiver is the default. A state bar sets the state filter.
3. **Receivers and MED** — CNAE and porte, then national MED. MED has no geography filter.

Questions live in the child collection `source questions`.

## What the seeded extract is

It is synthetic Parquet with the Olinda column names. It is not a download. `make ingest` still loads only `EstatisticasTransacoesPix`, `TransacoesPixPorMunicipio` and `ChavesPix`.

The as-of date is 25 November 2026, the same day as `docs/spike-bcb.md`. October 2026 is the last complete transaction month. MED stops at September 2026, and the banner says so. November 2026 is present and flagged incomplete, so the default filters do not use it. DICT user counts for 31 October 2026 match the figures in the spike (168,816,010 PF, 18,969,680 PJ, 187,785,690 total). Institution names on the key-stock table are sample names.

Municipality amounts are not forced to add up to the national cube.

## Again

A second `make metabase-provision` reuses `data/pix.duckdb` and replaces the questions and dashboards. To rebuild the extract, stop Metabase first. The driver holds the file.

```bash
make metabase-down
METABASE_REBUILD=1 make metabase-provision
make metabase-up
```

`make dbt-build` uses `PIX_RAW_ROOT` (default `data/raw`). If that zone has no MED, CNAE or DICT files, those facts become empty. Restore them with the rebuild above.

## Checks without the UI

```bash
make metabase-validate
```

That reads `dashboards/metabase/collection.json` and the SQL files. It does not start Docker. CI runs it next to `dbt build`.

## Filters the UI will not offer

MED and DICT users have no municipality filter. The age panel is national: it goes blank when a state or municipality filter is set, and a note says why. Distinct people stays empty until the result is a single municipality, because summing `QT_PES_*` across municipalities overcounts. Key stock is not labeled as users. Payer and receiver values are never added together.
