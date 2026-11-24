module "state" {
  source = "../modules/state_backend"

  bucket_name   = var.bucket_name
  force_destroy = var.force_destroy
}
