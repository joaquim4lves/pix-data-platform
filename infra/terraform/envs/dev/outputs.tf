output "aws_region" {
  description = "Region the stack was deployed to."
  value       = var.aws_region
}

output "bucket_name" {
  description = "Data lake bucket."
  value       = module.lake.bucket_name
}

output "log_bucket_name" {
  description = "Access-log bucket."
  value       = module.lake.log_bucket_name
}

output "bcb_function_name" {
  description = "BCB ingest Lambda."
  value       = module.bcb_ingest.function_name
}

output "bcb_schedules" {
  description = "EventBridge Scheduler names for the BCB ingest."
  value       = module.bcb_ingest.schedule_names
}

output "cdc_queue_name" {
  description = "Set CDC_QUEUE to this name for the local pgoutput consumer."
  value       = module.cdc_sink.queue_name
}

output "cdc_queue_url" {
  description = "CDC queue URL."
  value       = module.cdc_sink.queue_url
}

output "cdc_dlq_url" {
  description = "CDC dead-letter queue URL."
  value       = module.cdc_sink.dlq_url
}

output "cdc_function_name" {
  description = "CDC sink Lambda."
  value       = module.cdc_sink.function_name
}

output "glue_databases" {
  description = "Glue databases. Raw tables live in the raw database; views are created by transform/athena/views.sql."
  value       = module.catalog.database_names
}

output "glue_tables" {
  description = "External table names."
  value       = module.catalog.table_names
}

output "athena_workgroup" {
  description = "Workgroup with the enforced bytes-scanned cutoff."
  value       = module.athena.workgroup_name
}

output "athena_results" {
  description = "Query result location."
  value       = module.athena.results_location
}

output "budget_name" {
  description = "Monthly cost budget."
  value       = module.budgets.budget_name
}

output "github_deploy_role_arn" {
  description = "Store this as the GitHub variable AWS_DEPLOY_ROLE_ARN."
  value       = module.github_oidc.deploy_role_arn
}
