
resource "aws_lambda_function" "openpowerlifting_ingest" {
  function_name    = var.lambda_function_openpowerlifting.function_name
  role             = aws_iam_role.lambda_role.arn
  filename         = var.lambda_openpowerlifting_filename
  handler          = var.lambda_openpowerlifting_handler
  source_code_hash = filebase64sha256(var.lambda_openpowerlifting_filename)
  runtime          = var.lambda_function_openpowerlifting.runtime
  layers           = var.lambda_function_openpowerlifting.layers
  memory_size      = var.lambda_function_openpowerlifting.memory_size
  publish          = var.lambda_function_openpowerlifting.publish
  timeout          = var.lambda_function_openpowerlifting.timeout
}

resource "aws_lambda_permission" "daily_opl_ingest" {
  statement_id  = "AllowOpenpowerliftingLambdaFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.openpowerlifting_ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily.arn
}
