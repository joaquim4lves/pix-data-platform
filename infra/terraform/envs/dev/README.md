# envs/dev

The dev root. It wires the lake, the two Lambdas, the Glue catalog, the Athena workgroup, the budget, and the GitHub deploy role.

Postgres, the pgoutput consumer, Airflow, and Metabase are not in this root. They stay in Docker.

`terraform init -backend=false` and `terraform validate` need no AWS credentials. `plan` and `apply` need the Lambda zips from `infra/scripts/build_lambdas.sh`, a bootstrapped state bucket, and `budget_alert_email` plus `state_bucket_arn`. See [the runbook](../../../../docs/runbooks/aws-dev.md).
