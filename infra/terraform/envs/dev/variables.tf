variable "aws_region" {
  type        = string
  description = "AWS region. us-east-1 is the cheap default. sa-east-1 keeps the buckets in Sao Paulo."
  default     = "us-east-1"

  validation {
    condition     = contains(["us-east-1", "sa-east-1"], var.aws_region)
    error_message = "Use us-east-1 (default, lowest unit price) or sa-east-1 (Sao Paulo)."
  }
}

variable "environment" {
  type        = string
  description = "Environment slug used in resource names."
  default     = "dev"
}

variable "name_prefix" {
  type        = string
  description = "Prefix for AWS resource names."
  default     = "pix-data"
}

variable "catalog_prefix" {
  type        = string
  description = "Glue database prefix. Must match the Athena view script (default pix)."
  default     = "pix"
}

variable "bucket_name" {
  type        = string
  description = "Optional data lake bucket name. Empty uses <prefix>-<environment>-<account id>."
  default     = ""
}

variable "force_destroy" {
  type        = bool
  description = "Allow destroy to empty the dev buckets, including object versions."
  default     = true
}

variable "budget_alert_email" {
  type        = string
  description = "Inbox for the USD 5 monthly budget. Required at apply time."
  sensitive   = true
}

variable "budget_limit_usd" {
  type        = string
  description = "Monthly account-wide budget limit in USD."
  default     = "5"
}

variable "state_bucket_arn" {
  type        = string
  description = "ARN of the bootstrap state bucket. The deploy role may use only this bucket for state."
}

variable "github_repository" {
  type        = string
  description = "GitHub repository allowed to assume the deploy role."
  default     = "joaquim4lves/pix-data-platform"
}

variable "github_environment" {
  type        = string
  description = "GitHub environment the deploy workflow must declare."
  default     = "dev"
}

variable "existing_oidc_provider_arn" {
  type        = string
  description = "Existing GitHub OIDC provider ARN, when the account already has one."
  default     = ""
}

variable "bcb_zip_path" {
  type        = string
  description = "Zip produced by infra/scripts/build_lambdas.sh for the BCB ingest function."
  default     = ""
}

variable "cdc_zip_path" {
  type        = string
  description = "Zip produced by infra/scripts/build_lambdas.sh for the CDC sink."
  default     = ""
}

variable "athena_bytes_scanned_cutoff" {
  type        = number
  description = "Per-query Athena bytes-scanned cutoff. Default 1 GiB."
  default     = 1073741824
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention in days."
  default     = 14
}
