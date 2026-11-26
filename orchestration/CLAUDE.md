# Airflow

DAGs live in `orchestration/dags`: `bcb_pix_monthly`, `app_cdc_merge`, and `maintenance`. `make airflow-test` imports that package. It does not start the scheduler. `make airflow-up` is the compose profile `airflow` (apiserver, scheduler, dag processor). This is not MWAA.

`bcb_pix_monthly` maps one task per name from `ENTITY_ORDER`. Adding a live entity is a contract plus that tuple, not a new DAG. The Olinda pool serializes those tasks. `catchup` is false. The schedule is 07:00 America/Sao_Paulo on the 2nd.

Cosmos renders `transform/dbt` with `dbt_deps` off. dbt tasks take the `duckdb` pool because the file has one writer. Do not open a second writer against `data/pix.duckdb` while Metabase or another dbt run has it.
