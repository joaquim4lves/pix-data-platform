---
name: dbt-model
description: Add or change one dbt model with its YAML, tests, and docs, following the DuckDB project conventions. Use when creating a staging, intermediate, or mart model.
---

Read `transform/dbt/CLAUDE.md` and one neighboring model before writing SQL.

1. Put the file in `models/staging`, `models/intermediate`, or `models/marts`. Staging is the only layer that quotes Olinda column names. Later models use snake_case.
2. Materialization comes from `dbt_project.yml`: staging and intermediate are views; DuckDB marts are tables. Do not override that for a single model unless an ADR says so.
3. Measures are `decimal(38, 8)`. Do not cast a published BCB rate to a recomputed ratio. `PercentualdeDevolucao` stays as published.
4. Document the model and columns in the layer YAML (`_staging.yml`, `_intermediate.yml`, `_marts.yml`, or `_dashboard.yml` for the dashboard marts).
5. Add `unique` and `not_null` where the grain requires them, and a singular test under `transform/dbt/tests/` for a rule a column test cannot express (grain, `N/D`, SPI-only caption, complete-month flag).
6. A new raw source also needs `_BCB` in `transform/dbt_raw.py` and an `external_location` that uses `getvariable`. An empty glob must still build, via the sentinel the plugin writes.
7. Do not add the model to `transform/athena/views.sql`. That file is the legacy renderer. `tests/test_dbt_parity.py` compares the older models with `transform/sql`. If you change a model that test covers, update the oracle so the rows match. Do not delete the test.
8. Prove it with the fixture, then `make dbt-deps` and `make dbt-build`. The Athena target is not part of this check.
