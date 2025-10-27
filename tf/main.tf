terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67"
    }
  }

  required_version = ">= 1.11.0"

  backend "s3" {
    bucket = "dev-use2-tedsand-terraform-s3"
    key    = "backend/terraform.tfstate"
    region = "us-east-2"
  }
}

provider "aws" {
  region = "us-east-2"
}

locals {
  product = "tedsand"
  env     = "dev"
  tags = {
    product = local.product
    env     = local.env
  }
}
