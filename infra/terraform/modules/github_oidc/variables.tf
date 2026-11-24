variable "name" {
  type        = string
  description = "Resource name prefix, for example pix-data-dev."
}

variable "github_repository" {
  type        = string
  description = "GitHub repository allowed to assume the deploy role, as OWNER/NAME."

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "github_repository must look like owner/name."
  }
}

variable "github_environment" {
  type        = string
  description = "GitHub environment claim required on the OIDC token. The deploy workflow uses this environment."
  default     = "dev"
}

variable "workflow_path" {
  type        = string
  description = "Workflow file allowed to assume the role, relative to the repository root."
  default     = ".github/workflows/terraform-deploy.yml"
}

variable "existing_oidc_provider_arn" {
  type        = string
  description = "ARN of an existing token.actions.githubusercontent.com provider. Empty creates one."
  default     = ""
}

variable "state_bucket_arn" {
  type        = string
  description = "Bootstrap state bucket ARN. The role may read and write only this bucket for state."
}

variable "lake_bucket_arn" {
  type        = string
  description = "Data lake bucket ARN."
}

variable "log_bucket_arn" {
  type        = string
  description = "Data lake access-log bucket ARN."
}

variable "catalog_prefix" {
  type        = string
  description = "Glue database prefix the role may manage."
}
