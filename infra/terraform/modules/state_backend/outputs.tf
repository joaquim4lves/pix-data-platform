output "bucket_name" {
  description = "State bucket. Pass this to terraform init -backend-config=bucket=..."
  value       = aws_s3_bucket.state.id
}

output "bucket_arn" {
  description = "State bucket ARN. The GitHub deploy role is limited to this bucket for state."
  value       = aws_s3_bucket.state.arn
}

output "log_bucket_name" {
  description = "Access-log bucket for the state bucket."
  value       = aws_s3_bucket.logs.id
}
