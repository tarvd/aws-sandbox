resource "aws_iam_role" "lambda_role" {
  name        = "dev-tedsand-lambda-role"
  path        = "/service-role/"
  description = "Role for Lambda functions"
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonS3FullAccess",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
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
}

resource "aws_lambda_function" "openpowerlifting_ingest" {
  function_name    = "dev-use2-tedsand-openpowerlifting-ingest-lambda"
  role             = aws_iam_role.lambda_role.arn
  filename         = var.lambda_openpowerlifting_filename
  handler          = var.lambda_openpowerlifting_handler
  source_code_hash = filebase64sha256(var.lambda_openpowerlifting_filename)
  runtime          = "python3.9"
  layers = [
    "arn:aws:lambda:us-east-2:336392948345:layer:AWSSDKPandas-Python313:1",
  ]
  memory_size = 3008
  publish     = false
  timeout     = 60
}

resource "aws_cloudwatch_event_rule" "daily" {
  name                = "dev-use2-tedsand-daily-cw-rule"
  schedule_expression = "cron(0 18 ? * * *)"
  description         = "Daily rule to trigger Lambda function"
  tags = merge(
    local.tags,
    { name = "daily-rule" }
  )
}

resource "aws_cloudwatch_event_target" "daily_opl_ingest" {
  target_id = "dev-use2-tedsand-daily-opl-ingest-target"
  rule      = aws_cloudwatch_event_rule.daily.name
  arn       = aws_lambda_function.openpowerlifting_ingest.arn
}

resource "aws_lambda_permission" "daily_opl_ingest" {
  statement_id  = "AllowOpenpowerliftingLambdaFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.openpowerlifting_ingest.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily.arn
}
