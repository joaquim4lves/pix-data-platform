output "name" {
  description = "Glue table name."
  value       = aws_glue_catalog_table.this.name
}

output "arn" {
  description = "Glue table ARN."
  value       = aws_glue_catalog_table.this.arn
}
