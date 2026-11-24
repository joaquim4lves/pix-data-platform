resource "aws_glue_catalog_table" "this" {
  name          = var.name
  database_name = var.database_name
  description   = var.description
  table_type    = "EXTERNAL_TABLE"

  parameters = merge(
    {
      EXTERNAL                    = "TRUE"
      classification              = "parquet"
      "projection.enabled"        = "true"
      "storage.location.template" = var.location_template
    },
    var.projection,
  )

  storage_descriptor {
    location      = var.location
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    dynamic "columns" {
      for_each = var.columns
      content {
        name = columns.value.name
        type = columns.value.type
      }
    }
  }

  dynamic "partition_keys" {
    for_each = var.partition_keys
    content {
      name = partition_keys.value.name
      type = partition_keys.value.type
    }
  }
}
