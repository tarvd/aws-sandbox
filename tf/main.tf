terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.67"
    }
  }

  required_version = ">= 1.11.0"

  backend "s3" {
    bucket = "ted-sand-dev-s3-use2-terraform"
    key    = "backend/terraform.tfstate"
    region = "us-east-2"
  }
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
