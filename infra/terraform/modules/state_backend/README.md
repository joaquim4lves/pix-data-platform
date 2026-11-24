# state_backend

S3 bucket for Terraform state, with versioning, SSE-S3, public access blocked, and access logs.

Locking uses Terraform's native S3 lockfile (`use_lockfile = true` in the backend block), which needs Terraform 1.10 or newer. A DynamoDB lock table is not created. The bootstrap root calls this module and keeps its own state on local disk, so the state bucket does not have to exist before it is created.
