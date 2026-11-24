# Terraform

Low-cost AWS account for the PIX lake. The layout:

```text
bootstrap/                 state bucket, local state, applied once
envs/dev/                  the account: lake, Lambdas, catalog, Athena, budget, OIDC
modules/lake               S3 data lake and access logs
modules/state_backend      S3 state bucket and access logs
modules/bcb_ingest         scheduled BCB Lambda
modules/cdc_sink           SQS, DLQ, CDC Lambda, partial-batch responses
modules/catalog            Glue databases and partition projection
modules/glue_parquet_table one external table
modules/athena             workgroup with a bytes-scanned cutoff
modules/budgets            USD 5 monthly budget
modules/github_oidc        GitHub Actions OIDC deploy role
```

Postgres and Airflow stay in Docker. Nothing here creates an EC2 instance, an RDS database, a load balancer, or a NAT gateway.

Region default is `us-east-1`. Set `aws_region = "sa-east-1"` for Sao Paulo. The cost notes are in [docs/cost-estimate.md](../../docs/cost-estimate.md). Deploy and destroy steps are in [docs/runbooks/aws-dev.md](../../docs/runbooks/aws-dev.md). The decision record is [docs/adr/ADR-004.md](../../docs/adr/ADR-004.md).

`terraform init -backend=false` and `terraform validate` do not need credentials and do not apply anything.
