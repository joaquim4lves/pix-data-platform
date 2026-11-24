# bootstrap

Creates the remote state bucket and its access-log bucket. State for this root stays on local disk (`terraform.tfstate`, gitignored).

Locking for `envs/dev` is the S3 lockfile (`use_lockfile = true`), not DynamoDB. DynamoDB still works if you add a table later and set `use_lockfile = false` plus `dynamodb_table` in the backend block. This stack does not create that table.

Apply this root once with an administrator, then point `envs/dev` at the bucket. Do not commit the local state file.
