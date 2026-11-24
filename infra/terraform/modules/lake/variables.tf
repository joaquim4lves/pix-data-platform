variable "name_prefix" {
  type        = string
  description = "Short DNS-safe prefix. The default bucket name is <prefix>-<environment>-<account id>."

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{1,20}$", var.name_prefix))
    error_message = "name_prefix must be lowercase letters, digits, and hyphens."
  }
}

variable "environment" {
  type        = string
  description = "Environment name used in the bucket and in tags."

  validation {
    condition     = can(regex("^[a-z0-9-]{2,12}$", var.environment))
    error_message = "environment must be a short lowercase slug."
  }
}

variable "bucket_name" {
  type        = string
  description = "Override the data lake bucket name. Empty uses the account-scoped default."
  default     = ""
}

variable "force_destroy" {
  type        = bool
  description = "Delete objects, including versions, on terraform destroy. Dev sets this true."
  default     = false
}

variable "athena_results_expiration_days" {
  type        = number
  description = "Days before objects under athena-results/ expire."
  default     = 7
}

variable "quarantine_expiration_days" {
  type        = number
  description = "Days before objects under quarantine/ expire."
  default     = 30
}

variable "noncurrent_version_expiration_days" {
  type        = number
  description = "Days before a noncurrent object version expires. Current Parquet is kept."
  default     = 30
}

variable "log_expiration_days" {
  type        = number
  description = "Days before server access logs expire."
  default     = 90
}
