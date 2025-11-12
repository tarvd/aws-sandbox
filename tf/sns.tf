resource "aws_sns_topic" "lambda_results" {
  name         = var.sns_topic_lambda_results.name
  display_name = var.sns_topic_lambda_results.display_name
  policy       = templatefile(
    var.sns_topic_lambda_results.policy_file,
    {
      aws_account_id   = var.aws_account_id
    }
  )
}

resource "aws_sns_topic_subscription" "lambda_results_email" {
  topic_arn = aws_sns_topic.lambda_results.arn
  protocol = "email"
  endpoint = var.sns_email
}