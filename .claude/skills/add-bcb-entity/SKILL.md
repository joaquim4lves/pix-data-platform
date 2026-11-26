---
name: add-bcb-entity
description: Add one Olinda PIX entity from contract through raw Parquet, dbt, tests, and the Airflow ingest task. Use when wiring a new BCB feed such as MED, CNAE, or DICT users.
---

Read `docs/spike-bcb.md` and `ingestion/bcb/entities.py` first. Copy an existing entity. Do not infer columns from the Portuguese name.

1. Confirm the resource. Working reads are function imports (`Database`, `DataBase`, or `Data`). Underscore entity sets return HTTP 500. `PixUsuariosCadastradosDICT` is an entity set and needs its own read path. It is not a function import.
2. Add the Pydantic model (`extra=forbid`), the PyArrow schema, and an `EntitySpec`. Decimal measures use `decimal128(38, 8)`. Keep raw codes. `NATUREZA` on transactions is the nine codes in `NATUREZA_CODES`.
3. Add the spec to `ENTITY_ORDER` only when `make ingest` should load it. MED (`EstatisticasFraudesPix`), CNAE (`CnaePorteRecebedor`), and DICT users already have specs and are not in `ENTITY_ORDER`. The monthly DAG maps `ENTITY_ORDER`, so a new live entity does not need a new DAG file.
4. Register the variable in `_BCB` inside `transform/dbt_raw.py`. The variable name is `pix_raw_<source_table>`. Add the source table in `transform/dbt/models/staging/_sources.yml` with `external_location` calling `read_parquet(getvariable('pix_raw_<source_table>'), ...)`, matching the existing tables. Partition is `raw/bcb/<EntityName>/ano_mes=YYYYMM`.
5. Add `stg_<source>.sql`. Quote Olinda names in that file only. Cast measures to `decimal(38, 8)`. Filter a null period key. Document columns in `transform/dbt/models/staging/_staging.yml`.
6. Add a mart only when a dashboard needs a new grain. Say "contested via MED", never "fraud", for MED counts. The MED-to-SPI ratio stays SPI-only and is not an official BCB rate. Keep the municipality `N/D` row and its null IBGE code. Do not checkpoint the in-progress America/Sao_Paulo month.
7. Extend the fixture writer and a pytest that builds the schema. Add a singular dbt test for the grain. Run `make test` and `make dbt-build` on fixture Parquet (`write_sample_raw`). Do not require a live Olinda call in CI.
