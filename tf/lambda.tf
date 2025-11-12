
resource "aws_lambda_function" "openpowerlifting_ingest" {
  filename         = var.lambda_openpowerlifting_filename
  handler          = var.lambda_openpowerlifting_handler
  function_name    = var.lambda_function_openpowerlifting.function_name
  runtime          = var.lambda_function_openpowerlifting.runtime
  layers           = var.lambda_function_openpowerlifting.layers
  memory_size      = var.lambda_function_openpowerlifting.memory_size
  publish          = var.lambda_function_openpowerlifting.publish
  timeout          = var.lambda_function_openpowerlifting.timeout
  source_code_hash = filebase64sha256(var.lambda_openpowerlifting_filename)

  role             = aws_iam_role.lambda_role.arn
}

resource "aws_lambda_permission" "daily_opl_ingest" {
  statement_id  = "AllowOpenpowerliftingLambdaFromEventBridge"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"

  function_name = var.lambda_function_openpowerlifting.function_name

  source_arn    = aws_cloudwatch_event_rule.daily.arn
}
