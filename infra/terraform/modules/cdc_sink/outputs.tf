output "queue_name" {
  description = "Queue name. Set CDC_QUEUE to this when the local consumer publishes to AWS."
  value       = aws_sqs_queue.cdc.name
}

output "queue_url" {
  description = "CDC queue URL."
  value       = aws_sqs_queue.cdc.url
}

output "queue_arn" {
  description = "CDC queue ARN."
  value       = aws_sqs_queue.cdc.arn
}

output "dlq_url" {
  description = "Dead-letter queue URL."
  value       = aws_sqs_queue.dlq.url
}

output "function_name" {
  description = "CDC sink Lambda name."
  value       = aws_lambda_function.sink.function_name
}

output "function_arn" {
  description = "CDC sink Lambda ARN."
  value       = aws_lambda_function.sink.arn
}

output "event_source_mapping_uuid" {
  description = "SQS event source mapping. Partial failures use ReportBatchItemFailures."
  value       = aws_lambda_event_source_mapping.cdc.uuid
}
