# Terraform

`make tf-check` is the only automated Terraform command. It runs `terraform fmt -check`, then `init -backend=false` and `validate` in `bootstrap/` and `envs/dev/`. Those steps do not need credentials and do not apply.

Do not run `terraform apply`, `terraform destroy`, or `terraform plan` against a real backend. Do not create `*.tfvars` or `backend.hcl`. State, plans, and the `.terraform/` directory stay untracked.

The design has no EC2, RDS, load balancer, or NAT gateway. Postgres, Airflow, and Metabase stay in Docker. The deploy workflow is `workflow_dispatch` and skips when its repository variables are unset. An agent does not dispatch it.
