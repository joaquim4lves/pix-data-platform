locals {
  name    = "${var.name_prefix}-${var.environment}"
  bcb_zip = var.bcb_zip_path != "" ? var.bcb_zip_path : "${path.module}/../../build/bcb_ingest.zip"
  cdc_zip = var.cdc_zip_path != "" ? var.cdc_zip_path : "${path.module}/../../build/cdc_sink.zip"
}

module "lake" {
  source = "../../modules/lake"

  name_prefix   = var.name_prefix
  environment   = var.environment
  bucket_name   = var.bucket_name
  force_destroy = var.force_destroy
}

module "bcb_ingest" {
  source = "../../modules/bcb_ingest"

  name                 = local.name
  bucket_name          = module.lake.bucket_name
  bucket_arn           = module.lake.bucket_arn
  bucket_versioning_id = module.lake.versioning_id
  zip_path             = local.bcb_zip
  log_retention_days   = var.log_retention_days
}

module "cdc_sink" {
  source = "../../modules/cdc_sink"

  name                 = local.name
  bucket_name          = module.lake.bucket_name
  bucket_arn           = module.lake.bucket_arn
  bucket_versioning_id = module.lake.versioning_id
  zip_path             = local.cdc_zip
  log_retention_days   = var.log_retention_days
}

module "catalog" {
  source = "../../modules/catalog"

  catalog_prefix = var.catalog_prefix
  bucket_name    = module.lake.bucket_name
}

module "athena" {
  source = "../../modules/athena"

  name                 = local.name
  results_bucket       = module.lake.bucket_name
  bytes_scanned_cutoff = var.athena_bytes_scanned_cutoff
}

module "budgets" {
  source = "../../modules/budgets"

  name        = local.name
  limit_usd   = var.budget_limit_usd
  alert_email = var.budget_alert_email
}

module "github_oidc" {
  source = "../../modules/github_oidc"

  name                       = local.name
  github_repository          = var.github_repository
  github_environment         = var.github_environment
  existing_oidc_provider_arn = var.existing_oidc_provider_arn
  state_bucket_arn           = var.state_bucket_arn
  lake_bucket_arn            = module.lake.bucket_arn
  log_bucket_arn             = module.lake.log_bucket_arn
  catalog_prefix             = var.catalog_prefix
}
