resource "aws_iam_group" "admin" {
  name = var.iam_group_admin_name
}

resource "aws_iam_user" "tdouglas" {
  name = var.iam_user_admin_name
}

resource "aws_iam_role" "glue_job_role" {
  name               = var.iam_role_glue_job.name
  description        = var.iam_role_glue_job.description
  assume_role_policy = "${file(var.iam_role_glue_job.assume_role_policy_file)}"
}

resource "aws_iam_policy" "glue_job_policy" {
  name        = var.iam_role_glue_job.policy_name
  policy      = templatefile(
    var.iam_role_glue_job.policy_file,
    {
      python_s3_bucket   = "${aws_s3_bucket.python.bucket}"
      raw_data_s3_bucket = "${aws_s3_bucket.raw_data.bucket}"
      iceberg_s3_bucket  = "${aws_s3_bucket.iceberg.bucket}"
      athena_s3_bucket  = "${aws_s3_bucket.athena_results.bucket}"
    })
}

resource "aws_iam_role_policy_attachment" "glue_job_attach" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = aws_iam_policy.glue_job_policy.arn
}

resource "aws_iam_role_policy_attachment" "glue-job-role-sns-policy-attach" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = aws_iam_policy.lambda_results_publish_to_sns.arn
}

resource "aws_iam_role_policy_attachment" "glue-job-role-athena-policy-attach" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = data.aws_iam_policy.AmazonAthenaFullAccess.arn
}

resource "aws_iam_role" "glue_notebook_role" {
  name               = var.iam_role_glue_notebook.name 
  description        = var.iam_role_glue_notebook.description
  assume_role_policy = "${file(var.iam_role_glue_notebook.assume_role_policy_file)}"
}

resource "aws_iam_policy" "glue_notebook_policy" {
  name        = var.iam_role_glue_notebook.policy_name
  policy      = templatefile(
    var.iam_role_glue_notebook.policy_file,
    {
      python_s3_bucket   = aws_s3_bucket.python.bucket
      raw_data_s3_bucket = aws_s3_bucket.raw_data.bucket
      iceberg_s3_bucket  = aws_s3_bucket.iceberg.bucket
    })
}

resource "aws_iam_role_policy_attachment" "glue_notebook_attach" {
  role       = aws_iam_role.glue_notebook_role.name
  policy_arn = aws_iam_policy.glue_notebook_policy.arn
}

resource "aws_iam_role" "lambda_role" {
  name        = var.iam_role_lambda.name
  description = var.iam_role_lambda.description
  assume_role_policy = "${file(var.iam_role_lambda.assume_role_policy_file)}"
}

data "aws_iam_policy" "AmazonS3FullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-role-s3-policy-attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = data.aws_iam_policy.AmazonS3FullAccess.arn
}

data "aws_iam_policy" "AmazonAthenaFullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-role-athena-policy-attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = data.aws_iam_policy.AmazonAthenaFullAccess.arn
}

data "aws_iam_policy" "AWSLambdaBasicExecutionRole" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda-role-lambda-policy-attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = data.aws_iam_policy.AWSLambdaBasicExecutionRole.arn
}

resource "aws_iam_policy" "lambda_results_publish_to_sns" {
  name        = var.iam_policy_lambda_results_publish_to_sns_name
  policy      = templatefile(
    var.iam_role_lambda.sns_policy_file,
    {
      sns_topic_arn   = aws_sns_topic.lambda_results.arn
    })
}

resource "aws_iam_role_policy_attachment" "lambda-role-sns-policy-attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_results_publish_to_sns.arn
}

resource "aws_iam_role" "eb_start_workflow" {
  name               = var.iam_role_eventbridge_start_workflow.name 
  description        = var.iam_role_eventbridge_start_workflow.description
  assume_role_policy = "${file(var.iam_role_eventbridge_start_workflow.assume_role_policy_file)}"
}

resource "aws_iam_policy" "eb_start_workflow" {
  name        = var.iam_role_eventbridge_start_workflow.policy_name
  policy      = "${file(var.iam_role_eventbridge_start_workflow.policy_file)}"
}

resource "aws_iam_role_policy_attachment" "eb_start_workflow" {
  role       = aws_iam_role.eb_start_workflow.name
  policy_arn = aws_iam_policy.eb_start_workflow.arn
}

resource "aws_iam_role_policy_attachment" "eventbridge_workflow_sns" {
  role       = aws_iam_role.eb_start_workflow.name
  policy_arn = aws_iam_policy.lambda_results_publish_to_sns.arn
}
