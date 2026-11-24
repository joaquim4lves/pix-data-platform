terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  # Bucket and region come from -backend-config so this file can be
  # validated with `terraform init -backend=false` and no AWS account.
  # Locking is Terraform's S3 lockfile (1.10+), not a DynamoDB table.
  backend "s3" {
    key          = "env/dev/terraform.tfstate"
    use_lockfile = true
    encrypt      = true
  }
}
