provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "pix-data-platform"
      Environment = "bootstrap"
      ManagedBy   = "terraform"
    }
  }
}
