terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67"
    }
  }

  required_version = ">= 1.11.0"
}

provider "aws" {
  region = "us-east-2"
}

locals {
  org     = "ted"
  product = "sand"
  env     = "dev"
  tags = {
    org     = local.org
    product = local.product
    env     = local.env
  }
}
