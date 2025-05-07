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
