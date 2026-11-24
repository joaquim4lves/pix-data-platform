variable "database_name" {
  type        = string
  description = "Glue database that owns the table."
}

variable "name" {
  type        = string
  description = "Glue table name. Staging SQL uses this name under the raw database."
}

variable "description" {
  type        = string
  description = "Table comment shown in the catalog."
}

variable "columns" {
  type = list(object({
    name = string
    type = string
  }))
  description = "Parquet columns. Partition keys are not repeated here."
}

variable "partition_keys" {
  type = list(object({
    name = string
    type = string
  }))
  description = "Hive partition columns projected by Athena. No partitions are added by a crawler."
}

variable "location" {
  type        = string
  description = "S3 prefix that holds every partition of this table."
}

variable "location_template" {
  type        = string
  description = "storage.location.template. Partition placeholders use Glue syntax, for example $${ano_mes}."
}

variable "projection" {
  type        = map(string)
  description = "projection.<column>.* parameters. projection.enabled is set by the module."
}
