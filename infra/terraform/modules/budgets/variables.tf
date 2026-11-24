variable "name" {
  type        = string
  description = "Budget name prefix. The budget itself is named <name>-monthly."
}

variable "limit_usd" {
  type        = string
  description = "Monthly cost limit in USD. The default is the portfolio cap."
  default     = "5"
}

variable "alert_email" {
  type        = string
  description = "Inbox that receives the budget notifications. There is no default: apply must set one."
  sensitive   = true

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_email))
    error_message = "alert_email must look like an email address."
  }
}
