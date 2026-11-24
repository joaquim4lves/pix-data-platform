variable "catalog_prefix" {
  type        = string
  description = "Glue database prefix. pix_raw is the external tables; the other databases hold Athena views."

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,20}$", var.catalog_prefix))
    error_message = "catalog_prefix must be a lowercase Glue database prefix."
  }
}

variable "bucket_name" {
  type        = string
  description = "Data lake bucket. Raw prefixes are raw/bcb and raw/app."
}

variable "bcb_ano_mes_start" {
  type        = number
  description = "First YYYYMM included in the BCB partition enum. PIX open data starts at 202011."
  default     = 202011

  validation {
    condition     = var.bcb_ano_mes_start >= 202011 && var.bcb_ano_mes_start % 100 >= 1 && var.bcb_ano_mes_start % 100 <= 12
    error_message = "bcb_ano_mes_start must be a YYYYMM on or after 202011."
  }
}

variable "bcb_ano_mes_end" {
  type        = number
  description = "Last YYYYMM included in the BCB partition enum. Extend this when the range runs out."
  default     = 203512

  validation {
    condition     = var.bcb_ano_mes_end >= 202011 && var.bcb_ano_mes_end % 100 >= 1 && var.bcb_ano_mes_end % 100 <= 12
    error_message = "bcb_ano_mes_end must be a YYYYMM."
  }
}

variable "cdc_partition_start" {
  type        = string
  description = "First UTC date Athena will project for raw/app/dt=. NOW is the open end."
  default     = "2024-01-01"

  validation {
    condition     = can(regex("^\\d{4}-\\d{2}-\\d{2}$", var.cdc_partition_start))
    error_message = "cdc_partition_start must be YYYY-MM-DD."
  }
}
