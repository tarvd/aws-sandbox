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

resource "aws_lambda_function" "lambda_openpowerlifting_tf" {
  function_name = "ted-sand-dev-use2-ingest-openpowerlifting-tf"
  role = "arn:aws:iam::820242901733:role/service-role/LambdaIngestPowerliftingRole"
  filename = "../python/lambda_ingest_openpowerlifting.zip"
  handler = "lambda_ingest_openpowerlifting.lambda_handler"
  runtime = "python3.9"
  layers = [
    "arn:aws:lambda:us-east-2:336392948345:layer:AWSSDKPandas-Python313:1",
  ]
  memory_size = 3008
  publish = false
  timeout = 60
  tags = {
    org = "ted"
    product = "sand"
    env = "dev"
    name = "openpowerlifting-lambda-tf"
  }
}
