terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region = "us-east-2"
}

resource "aws_s3_bucket" "s3_athena" {
  bucket = "ted-sand-dev-s3-use2-athena"

  tags = {
    org = "ted"
    product = "sand"
    env = "dev"
    name = "athena-s3"
  }
}

resource "aws_s3_bucket" "s3_data" {
  bucket = "ted-sand-dev-s3-use2-data"

  tags = {
    org = "ted"
    product = "sand"
    env = "dev"
    name = "data-s3"
  }
}

resource "aws_s3_bucket" "s3_lambda" {
  bucket = "ted-sand-dev-s3-use2-lambda"

  tags = {
    org = "ted"
    product = "sand"
    env = "dev"
    name = "lambda-s3"
  }
}
