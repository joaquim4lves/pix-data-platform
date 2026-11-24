output "database_names" {
  description = "Glue database name for each schema (raw, seeds, staging, intermediate, marts, checks)."
  value       = { for key, db in aws_glue_catalog_database.schema : key => db.name }
}

output "raw_database" {
  description = "Database that holds the external Parquet tables."
  value       = aws_glue_catalog_database.schema["raw"].name
}

output "table_names" {
  description = "External table names in the raw database."
  value       = concat(keys(module.bcb), keys(module.app))
}
