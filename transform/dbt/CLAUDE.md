# dbt

Project name `pix_data_platform`. Directory `transform/dbt`. Entrypoint is `python -m transform.dbt_main`, which `make dbt-deps`, `make dbt-build`, and `make dbt-docs` call. `dbt build` is the test run. There is no separate test target.

Staging quotes Olinda identifiers once and emits snake_case. Measures stay `decimal(38, 8)`. Describe the model in the layer YAML. Put grain and domain checks in `transform/dbt/tests/`. `packages.yml` is empty, so Cosmos does not run `dbt deps` inside the DAG.

DuckDB is the local and CI target. `dbt build --target athena` is manual and has not been run against AWS. Do not point a slice at Athena to make a test pass. `transform/sql` is the parity oracle. Change it only when the parity test requires the same rows, not to silence a failure.

Empty `pix_as_of_date` means the America/Sao_Paulo clock. `make metabase-provision` sets `2026-11-25` so the seeded story stays put.
