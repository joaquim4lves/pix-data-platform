terraform {
  required_version = ">= 1.10.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }

  # Local on purpose. This root creates the bucket the other roots use,
  # so it cannot store its own state there on the first apply.
  backend "local" {
    path = "terraform.tfstate"
  }
}
