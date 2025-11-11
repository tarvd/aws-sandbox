resource "aws_cloudwatch_event_rule" "daily" {
  name                = "dev-use2-tedsand-daily-eb-rule"
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

resource "aws_cloudwatch_event_rule" "openpowerlifting" {
  name                = "dev-use2-tedsand-openpowerlifting-eb-rule"
  description         = "EB Rule for triggering a Glue Workflow to process new raw data from Openpowerlifting.org"
  event_pattern       = jsonencode(
    {
        "source": ["aws.s3"],
        "detail-type": ["Object Created"],
        "detail": {
            "bucket": {
            "name": ["dev-use2-tedsand-raw-data-s3"]
            },
            "object": {
            "key": [{
                "prefix": "openpowerlifting"
            }]
            }
        }
    }
  )
}

resource "aws_cloudwatch_event_target" "s3_openpowerlifting" {
  target_id = "dev-use2-tedsand-s3-openpowerlifting-target"
  rule      = aws_cloudwatch_event_rule.openpowerlifting.name
  arn       = aws_glue_workflow.openpowerlifting.arn
  role_arn  = aws_iam_role.eb_start_workflow.arn
}
