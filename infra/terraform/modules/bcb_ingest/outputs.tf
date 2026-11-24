output "function_name" {
  description = "BCB ingest Lambda name."
  value       = aws_lambda_function.bcb.function_name
}

output "function_arn" {
  description = "BCB ingest Lambda ARN."
  value       = aws_lambda_function.bcb.arn
}

output "role_arn" {
  description = "Execution role ARN."
  value       = aws_iam_role.bcb.arn
}

output "schedule_names" {
  description = "Scheduler names keyed by the schedule map key."
  value       = { for key, schedule in aws_scheduler_schedule.bcb : key => schedule.name }
}

output "dlq_url" {
  description = "Dead-letter queue for failed schedules and async invokes."
  value       = aws_sqs_queue.dlq.url
}

output "log_group_name" {
  description = "CloudWatch log group."
  value       = aws_cloudwatch_log_group.bcb.name
}
