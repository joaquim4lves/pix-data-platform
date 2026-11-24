variable "name" {
  type        = string
  description = "Resource name prefix, for example pix-data-dev."
}

variable "bucket_name" {
  type        = string
  description = "Data lake bucket the function writes."
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

variable "schedules" {
  type        = map(string)
  description = "EventBridge Scheduler expressions, keyed by a short name. Timezone is schedule_timezone."
  default = {
    daily   = "cron(0 8 * * ? *)"
    monthly = "cron(0 8 2 * ? *)"
  }

  validation {
    condition     = alltrue([for key, expression in var.schedules : can(regex("^[A-Za-z0-9]+$", key)) && length(expression) > 0])
    error_message = "Schedule keys must be alphanumeric. They are copied into a Lambda permission id."
  }
}

variable "schedule_timezone" {
  type        = string
  description = "IANA timezone for the BCB schedules. The watermark calendar is America/Sao_Paulo."
  default     = "America/Sao_Paulo"
}

variable "lookback_months" {
  type        = number
  description = "LOOKBACK_MONTHS passed to the ingest handler."
  default     = 3
}

variable "memory_mb" {
  type        = number
  description = "Lambda memory. 1024 MB is enough to import PyArrow."
  default     = 1024
}

variable "timeout_seconds" {
  type        = number
  description = "Lambda timeout. Olinda can be slow, and the handler reads several months."
  default     = 900
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention. Short on purpose."
  default     = 14
}

variable "reserved_concurrency" {
  type        = number
  description = "Cap on concurrent ingest invocations."
  default     = 2
}
