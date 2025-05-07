resource "aws_iam_role" "lambda_ingest_powerlifting_role" {
  name = "LambdaIngestPowerliftingRole"
  path = "/service-role/"
  description = "Role for Lambda function to ingest Open Powerlifting data"
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

  tags = merge(
    local.tags,
    {name = "ingest-openpowerlifting-iam-role"}
  )
}

resource "aws_lambda_function" "lambda_openpowerlifting_tf" {
  function_name = "ted-sand-dev-use2-ingest-openpowerlifting-tf"
  role = aws_iam_role.lambda_ingest_powerlifting_role.arn
  filename = var.lambda_openpowerlifting_filename
  handler = var.lambda_openpowerlifting_handler
  source_code_hash = filebase64sha256(var.lambda_openpowerlifting_filename)
  runtime = "python3.9"
  layers = [
    "arn:aws:lambda:us-east-2:336392948345:layer:AWSSDKPandas-Python313:1",
  ]
  memory_size = 3008
  publish = false
  timeout = 60
  tags = merge(
    local.tags,
    {name = "openpowerlifting-lambda-tf"}
  )
}

resource "aws_cloudwatch_event_rule" "daily_rule" {
  name = "daily_rule"
  schedule_expression = "cron(0 18 ? * * *)"
  description = "Daily rule to trigger Lambda function"
  tags = merge(
    local.tags,
    {name = "daily-rule"}
  )
}

resource "aws_cloudwatch_event_target" "lambda_target_openpowerlifting" {
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
