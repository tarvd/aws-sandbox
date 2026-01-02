resource "archive_file" "openpowerlifting_ingest_zip" {
  type        = "zip"
  source_file = var.lambda_openpowerlifting_py_file
  output_path = var.lambda_openpowerlifting_archive
}

data "archive_file" "utils_layer" {
  type        = "zip"
  source_dir  = var.lambda_layer_utils_directory
  output_path = var.lambda_layer_utils_archive
}

resource "aws_lambda_layer_version" "utils" {
  layer_name = "utils-layer"
  filename         = var.lambda_layer_utils_archive
  source_code_hash = data.archive_file.utils_layer.output_base64sha256
  compatible_runtimes = ["python3.13"]
  description = "Shared Python utilities for Lambdas"
}

resource "aws_lambda_function" "openpowerlifting_ingest" {
  filename         = var.lambda_openpowerlifting_archive
  handler          = var.lambda_openpowerlifting_handler
  function_name    = var.lambda_function_openpowerlifting.function_name
  runtime          = var.lambda_function_openpowerlifting.runtime
  layers           = [
    "arn:aws:lambda:us-east-2:336392948345:layer:AWSSDKPandas-Python313:1",
    aws_lambda_layer_version.utils.arn
  ]
  memory_size      = var.lambda_function_openpowerlifting.memory_size
  publish          = var.lambda_function_openpowerlifting.publish
  timeout          = var.lambda_function_openpowerlifting.timeout
  source_code_hash = archive_file.openpowerlifting_ingest_zip.output_base64sha256

  environment {
    variables = {
      URL = var.lambda_function_openpowerlifting.url
      BUCKET = aws_s3_bucket.raw_data.bucket
      SNS_TOPIC_ARN = aws_sns_topic.lambda_results.arn
      LAMBDA = var.lambda_function_openpowerlifting.function_name
    }
  }

  role             = aws_iam_role.lambda_role.arn
}

resource "aws_lambda_permission" "daily_opl_ingest" {
  statement_id  = "AllowOpenpowerliftingLambdaFromEventBridge"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"

  function_name = var.lambda_function_openpowerlifting.function_name

  source_arn    = aws_cloudwatch_event_rule.daily.arn
}
