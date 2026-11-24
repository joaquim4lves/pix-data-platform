output "workgroup_name" {
  description = "Workgroup that queries must use."
  value       = aws_athena_workgroup.this.name
}

output "workgroup_arn" {
  description = "Athena workgroup ARN."
  value       = aws_athena_workgroup.this.arn
}

output "results_location" {
  description = "S3 location of query results."
  value       = "s3://${var.results_bucket}/${var.results_prefix}"
}
