variable "aws_region" {
  type        = string
  description = "Region for the state bucket. Keep it the same as envs/dev."
  default     = "us-east-1"

  validation {
    condition     = contains(["us-east-1", "sa-east-1"], var.aws_region)
    error_message = "Use us-east-1 (default) or sa-east-1."
  }
}

variable "bucket_name" {
  type        = string
  description = "Globally unique state bucket name, for example pix-data-platform-tfstate-ACCOUNT_ID."
}

variable "force_destroy" {
  type        = bool
  description = "Allow destroy to delete state versions."
  default     = false
}
