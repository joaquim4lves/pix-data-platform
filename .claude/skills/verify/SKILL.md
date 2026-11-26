---
name: verify
description: Prove a change with the repo's lint, pytest, dbt, DAG import, and optional Metabase checks. Use before committing or when asked to show that it works.
---

Run the commands from the repository root. Quote the command and the result. A step you did not run is "not run", never "passed".

1. `make lint`
2. `make test`
3. Fixture Parquet, then dbt. `make dbt-build` needs the raw files or it replaces seeded MED, CNAE, and DICT facts with empty tables. On the current Makefile, `DBT` is assigned with `:=` before `PY` is set, so the recipe can become `m transform.dbt_main` and Make ignores the missing command. If the log says `m: No such file or directory`, run the same module yourself and do not treat that Make exit code as a dbt result. Do not reorder the Makefile while this branch is stacked on the Metabase PR.

```bash
python -c "from pathlib import Path; from tests.pix_warehouse import write_sample_raw; write_sample_raw(Path('data/raw'))"
make dbt-deps
make dbt-build
```

4. `make airflow-test` after `pip install -e '.[dev,airflow]'`. Skip only when the slice cannot import Airflow, and say so.
5. `make metabase-validate` checks the definition files and does not need Docker. `make metabase-up` and `make metabase-provision` are the UI smoke. Run them when Docker is available and the slice touches `dashboards/` or the dashboard marts. The UI is `http://localhost:3000`, user `pix@example.com`.
6. If Terraform files changed and `terraform` is on `PATH`, run `make tf-check`. Do not run `terraform plan`, `terraform apply`, or `terraform destroy`.
7. Do not start AWS. Do not read `.env` aloud.

Stop on the first failure and fix the code. Do not weaken a test. When the slice's feature in `docs/agentic/feature_list.json` has every step green, set that object's `passes` to true and append the session to `docs/agentic/progress.md`.
