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

resource "aws_iam_group" "admin" {
  name = "admin"
}

resource "aws_iam_user" "tdouglas" {
  name = "tdouglas"

  tags = {
    org = "ted"
    product = "sand"
    env = "dev"
    name = "tdouglas-iam-user"
    AKIA356SJNLSVAPD4LW2 = "cli"
  }
}

resource "aws_iam_role" "lambda_ingest_powerlifting_role" {
  name = "LambdaIngestPowerliftingRole"
  path = "/service-role/"
  description = "Role for Lambda function to ingest Open Powerlifting data"
  managed_policy_arns = [
    "arn:aws:iam::820242901733:policy/service-role/AWSLambdaBasicExecutionRole-c7c90f36-ad92-4754-a4b4-1d2afa342ef6",
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
  ]
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    org = "ted"
    product = "sand"
    env = "dev"
    name = "ingest-openpowerlifting-iam-role"
  }
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
  source_code_hash = filebase64sha256("../python/lambda_ingest_openpowerlifting.zip")
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

resource "aws_cloudwatch_event_rule" "daily_rule" {
  name = "daily_rule"
  schedule_expression = "cron(0 18 ? * * *)"
  description = "Daily rule to trigger Lambda function"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_rule.name
  target_id = "send-to-lambda-openpowerlifting-tf"
  arn       = aws_lambda_function.lambda_openpowerlifting_tf.arn
}

resource "aws_lambda_permission" "allow_eventbridge_openpowerlifting" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_openpowerlifting_tf.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_rule.arn
}

resource "aws_lambda_alias" "test_alias" {
  name             = "test_alias"
  function_name    = aws_lambda_function.lambda_openpowerlifting_tf.function_name
  function_version = "$LATEST"
}
