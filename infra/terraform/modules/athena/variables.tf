variable "name" {
  type        = string
  description = "Athena workgroup name. Queries must select this workgroup; primary is left alone."
}

variable "results_bucket" {
  type        = string
  description = "Bucket that receives query results."
}

variable "results_prefix" {
  type        = string
  description = "Prefix for query results, with a trailing slash."
  default     = "athena-results/"
}

variable "bytes_scanned_cutoff" {
  type        = number
  description = "Per-query bytes-scanned cutoff. Athena's minimum is 10 MiB. The default is 1 GiB."
  default     = 1073741824

  validation {
    condition     = var.bytes_scanned_cutoff >= 10485760
    error_message = "Athena rejects a bytes-scanned cutoff below 10 MiB (10485760)."
  }
}
