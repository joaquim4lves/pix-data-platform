output "bucket_name" {
  description = "Data lake bucket. Prefixes: raw/, curated/, athena-results/, quarantine/, artifacts/."
  value       = aws_s3_bucket.lake.id
}

output "bucket_arn" {
  description = "Data lake bucket ARN."
  value       = aws_s3_bucket.lake.arn
}

output "log_bucket_name" {
  description = "Server access log bucket for the data lake."
  value       = aws_s3_bucket.logs.id
}

output "log_bucket_arn" {
  description = "Server access log bucket ARN."
  value       = aws_s3_bucket.logs.arn
}

output "versioning_id" {
  description = "Versioning resource id. Lambda zip uploads wait on this."
  value       = aws_s3_bucket_versioning.lake.id
}
