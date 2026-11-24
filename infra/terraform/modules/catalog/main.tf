locals {
  contract   = jsondecode(file("${path.module}/columns.json"))
  schemas    = toset(["raw", "seeds", "staging", "intermediate", "marts", "checks"])
  start_year = tonumber(substr(tostring(var.bcb_ano_mes_start), 0, 4))
  end_year   = tonumber(substr(tostring(var.bcb_ano_mes_end), 0, 4))
  ano_mes_values = flatten([
    for year in range(local.start_year, local.end_year + 1) : [
      for month in range(1, 13) : format("%04d%02d", year, month)
      if(year * 100 + month) >= var.bcb_ano_mes_start && (year * 100 + month) <= var.bcb_ano_mes_end
    ]
  ])
  ano_mes_enum = join(",", local.ano_mes_values)
  bcb_tables   = { for item in local.contract.bcb : item.table => item }
  app_tables   = { for item in local.contract.app : item.table => item }
}

resource "aws_glue_catalog_database" "schema" {
  for_each = local.schemas

  name        = "${var.catalog_prefix}_${each.key}"
  description = "PIX ${each.key} schema. External tables use partition projection. Views are applied from transform/athena/views.sql."
}

module "bcb" {
  source   = "../glue_parquet_table"
  for_each = local.bcb_tables

  database_name = aws_glue_catalog_database.schema["raw"].name
  name          = each.value.table
  description   = each.value.description
  columns       = each.value.columns
  partition_keys = [
    { name = "ano_mes", type = "string" },
  ]
  location          = "s3://${var.bucket_name}/raw/bcb/${each.value.folder}/"
  location_template = "s3://${var.bucket_name}/raw/bcb/${each.value.folder}/ano_mes=$${ano_mes}"
  projection = {
    "projection.ano_mes.type"   = "enum"
    "projection.ano_mes.values" = local.ano_mes_enum
  }
}

module "app" {
  source   = "../glue_parquet_table"
  for_each = local.app_tables

  database_name = aws_glue_catalog_database.schema["raw"].name
  name          = each.value.table
  description   = each.value.description
  columns       = each.value.columns
  partition_keys = [
    { name = "dt", type = "date" },
  ]
  location          = "s3://${var.bucket_name}/raw/app/${each.value.folder}/"
  location_template = "s3://${var.bucket_name}/raw/app/${each.value.folder}/dt=$${dt}"
  projection = {
    "projection.dt.type"          = "date"
    "projection.dt.format"        = "yyyy-MM-dd"
    "projection.dt.range"         = "${var.cdc_partition_start},NOW"
    "projection.dt.interval"      = "1"
    "projection.dt.interval.unit" = "DAYS"
  }
}
