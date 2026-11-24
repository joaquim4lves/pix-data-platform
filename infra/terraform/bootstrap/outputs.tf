output "bucket_name" {
  description = "State bucket name. Use it as -backend-config bucket=..."
  value       = module.state.bucket_name
}

output "bucket_arn" {
  description = "State bucket ARN. Pass it to envs/dev as state_bucket_arn."
  value       = module.state.bucket_arn
}

output "log_bucket_name" {
  description = "Access-log bucket for the state bucket."
  value       = module.state.log_bucket_name
}

output "backend_config" {
  description = "Flags for terraform init in envs/dev."
  value       = "bucket=${module.state.bucket_name} region=${var.aws_region} use_lockfile=true encrypt=true"
}
