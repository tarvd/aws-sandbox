resource "archive_file" "openpowerlifting_ingest_zip" {
  type        = "zip"
  source_file = var.lambda_openpowerlifting_py_file
  output_path = var.lambda_openpowerlifting_archive
}

resource "aws_lambda_function" "openpowerlifting_ingest" {
  filename         = var.lambda_openpowerlifting_archive
  handler          = var.lambda_openpowerlifting_handler
  function_name    = var.lambda_function_openpowerlifting.function_name
  runtime          = var.lambda_function_openpowerlifting.runtime
  layers           = var.lambda_function_openpowerlifting.layers
  memory_size      = var.lambda_function_openpowerlifting.memory_size
  publish          = var.lambda_function_openpowerlifting.publish
  timeout          = var.lambda_function_openpowerlifting.timeout
  source_code_hash = archive_file.openpowerlifting_ingest_zip.output_base64sha256

  environment {
    variables = {
      URL = var.lambda_function_openpowerlifting.url
      BUCKET = aws_s3_bucket.raw_data.bucket
      PREFIX = var.lambda_function_openpowerlifting.s3_prefix
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
