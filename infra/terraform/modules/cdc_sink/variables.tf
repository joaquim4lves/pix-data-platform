variable "name" {
  type        = string
  description = "Resource name prefix, for example pix-data-dev."
}

variable "bucket_name" {
  type        = string
  description = "Data lake bucket the sink writes."
}

variable "bucket_arn" {
  type        = string
  description = "Data lake bucket ARN."
}

variable "bucket_versioning_id" {
  type        = string
  description = "Versioning resource id. The zip upload waits until versioning is on."
}

variable "zip_path" {
  type        = string
  description = "Path to the zip built by infra/scripts/build_lambdas.sh."
}

variable "memory_mb" {
  type        = number
  description = "Lambda memory. 1024 MB is enough to import PyArrow."
  default     = 1024
}

variable "timeout_seconds" {
  type        = number
  description = "Lambda timeout for one SQS batch."
  default     = 120
}

variable "visibility_timeout_seconds" {
  type        = number
  description = "SQS visibility timeout. Must be at least the Lambda timeout."
  default     = 720
}

variable "max_receive_count" {
  type        = number
  description = "Receives before a message is moved to the dead-letter queue."
  default     = 3
}

variable "batch_size" {
  type        = number
  description = "SQS records per Lambda invocation."
  default     = 10
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention. Short on purpose."
  default     = 14
}

variable "reserved_concurrency" {
  type        = number
  description = "Cap on concurrent sink invocations."
  default     = 5
}
