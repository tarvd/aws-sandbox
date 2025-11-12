resource "aws_cloudwatch_event_rule" "daily" {
  name                = var.eventbridge_rule_daily.name
  description         = var.eventbridge_rule_daily.description
  schedule_expression = var.eventbridge_rule_daily.schedule_expression
}

resource "aws_cloudwatch_event_target" "daily_opl_ingest" {
  target_id = var.eventbridge_rule_daily.target_id
  rule      = var.eventbridge_rule_daily.name

  arn       = aws_lambda_function.openpowerlifting_ingest.arn
}

resource "aws_cloudwatch_event_rule" "openpowerlifting" {
  name          = var.eventbridge_rule_new_data_openpowerlifting.name
  description   = var.eventbridge_rule_new_data_openpowerlifting.description
  event_pattern = jsonencode(
    {
      "source": ["aws.s3"],
      "detail-type": ["Object Created"],
      "detail": {
        "bucket": {
          "name": ["${var.eventbridge_rule_new_data_openpowerlifting.s3_bucket}"]
        },
        "object": {
          "key": [{
            "prefix": "${var.eventbridge_rule_new_data_openpowerlifting.s3_prefix}"
          }]
        }
      }
    }
  )
}

resource "aws_cloudwatch_event_target" "s3_openpowerlifting" {
  target_id = var.eventbridge_rule_new_data_openpowerlifting.target_id
  rule      = var.eventbridge_rule_new_data_openpowerlifting.name
  
  arn       = aws_glue_workflow.openpowerlifting.arn
  role_arn  = aws_iam_role.eb_start_workflow.arn
}
