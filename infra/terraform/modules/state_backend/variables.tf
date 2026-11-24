variable "bucket_name" {
  type        = string
  description = "Globally unique name for the Terraform state bucket."

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,55}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name must be a DNS-safe S3 name of at most 57 characters."
  }
}

variable "force_destroy" {
  type        = bool
  description = "Allow destroy to delete state versions. Leave false unless you are throwing the backend away."
  default     = false
}

variable "noncurrent_version_expiration_days" {
  type        = number
  description = "Days before a noncurrent state version expires. The current state object is kept."
  default     = 90
}
