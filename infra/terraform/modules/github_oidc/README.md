# github_oidc

GitHub Actions OIDC provider and one deploy role for this repository.

The trust policy requires the `environment` claim (default `dev`), a subject that is either a branch ref in this repository or the environment form, and `job_workflow_ref` pointing at `.github/workflows/terraform-deploy.yml`. Pull-request tokens do not match. The role can manage this project's buckets, functions, queues, catalog, workgroup, schedules, log groups, and the single monthly budget. It is not an administrator.

An AWS account can hold only one IAM OIDC provider for `token.actions.githubusercontent.com`. Set `existing_oidc_provider_arn` when that provider is already there.
