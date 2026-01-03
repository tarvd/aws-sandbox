
# Environment variables to set

# TF_VAR_aws_account_id
# TF_VAR_sns_email

# Top level vars

env = "dev"
region = "us-east-2"
region_short_code = "use2"
project = "tedsand"


# Athena workgroups

athena_workgroup_primary = {
  name = "primary"
  enforce_workgroup_configuration = true
  publish_cloudwatch_metrics_enabled = true
  encryption_option = "SSE_S3"
  acl_option = "BUCKET_OWNER_FULL_CONTROL"
}

athena_workgroup_dbt = {
  name = "dbt"
  enforce_workgroup_configuration = false
  publish_cloudwatch_metrics_enabled = true
  encryption_option = "SSE_S3"
  acl_option = "BUCKET_OWNER_FULL_CONTROL"
}


# Eventbridge rules and targets

eventbridge_rule_daily = {
  name = "dev-use2-tedsand-daily-eb-rule"
  description = "Daily rule to trigger Lambda function"
  schedule_expression = "cron(0 18 ? * * *)"
  target_id = "dev-use2-tedsand-s3-openpowerlifting-target"
}

eventbridge_rule_new_data_openpowerlifting = {
  name = "dev-use2-tedsand-openpowerlifting-eb-rule"
  description = "EB Rule for triggering a Glue Workflow to process new raw data from Openpowerlifting.org"
  s3_bucket = "dev-use2-tedsand-raw-data-s3"
  s3_prefix = "openpowerlifting"
  target_id = "dev-use2-tedsand-daily-opl-ingest-target"
  sns_target_id = "dev-use2-tedsand-opl-ingest-sns-target"
}


# Glue catalog databases and tables

glue_database_raw = {
  name = "raw"
  default_permissions = ["ALL"]
  lf_principal = "IAM_ALLOWED_PRINCIPALS"
}

glue_database_cleansed = {
  name = "cleansed"
  default_permissions = ["ALL"]
  lf_principal = "IAM_ALLOWED_PRINCIPALS"
}

glue_database_metadata = {
  name = "metadata"
  default_permissions = ["ALL"]
  lf_principal = "IAM_ALLOWED_PRINCIPALS"
}

glue_database_dbt = {
  name = "dbt"
  default_permissions = ["ALL"]
  lf_principal = "IAM_ALLOWED_PRINCIPALS"
}

glue_table_openpowerlifting_raw = {
  name = "openpowerlifting"
  database = "raw"
  table_type = "EXTERNAL_TABLE"
  classification = "csv"
  skip_header_line_count = "1"
  s3_prefix = "openpowerlifting"
  input_format = "org.apache.hadoop.mapred.TextInputFormat"
  output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"
  compressed = false
  serialization_library = "org.apache.hadoop.hive.serde2.OpenCSVSerde"
  separation_char = ","
}


# Glue ETL jobs, workflows, and triggers

py_utils_src = "../python/utils"
py_utils_build = "../build/utils.zip"
py_utils_s3_key = "libs/utils.zip"

glue_job_openpowerlifting_cleanse = {
    name              = "dev-use2-tedsand-openpowerlifting-cleanse-job"
    description       = "Job to source data from Openpowerlifting Raw Data to Iceberg Cleansed Table"
    glue_version      = "5.0"
    max_retries       = 0
    timeout           = 30
    number_of_workers = 4
    worker_type       = "G.1X"
    execution_class   = "STANDARD"
    command           = "glueetl"
    script            = "../python/glue/openpowerlifting_cleanse_job.py"
    s3_key            = "glue/openpowerlifting_cleanse_job.py"
    default_arguments = {
      "--job-language"                     = "python"
      "--continuous-log-logGroup"          = "/aws-glue/jobs"
      "--enable-continuous-cloudwatch-log" = "true"
      "--enable-continuous-log-filter"     = "true"
      "--enable-auto-scaling"              = "false"
      "--conf"                             = "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog --conf spark.sql.catalog.glue_catalog.warehouse=s3://dev-use2-tedsand-iceberg-s3/warehouse/ --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO"
      "--datalake-formats"                 = "iceberg"
      "--job-bookmark-option"              = "job-bookmark-disable"
      "--TempDir"                          = "s3://aws-glue-assets-820242901733-us-east-2/temp/"
      "--enable-glue-datacatalog"          = "true"
      "--enable-job-insights"              = "true"
      "--enable-metrics"                   = "true"
      "--enable-spark-ui"                  = "true"
      "--spark-event-logs-path"            = "s3://dev-use2-tedsand-logs-s3/spark-ui/"
    }
}

glue_workflow_openpowerlifting = {
  name = "dev-use2-tedsand-openpowerlifting-wf"
  description = "Glue workflow to process Openpowerlifting.org data"
  max_concurrent_runs = 1
}

glue_trigger_openpowerlifting_cleanse = {
  name = "dev-use2-tedsand-openpowerlifting-cleanse-tr"
  workflow = "dev-use2-tedsand-openpowerlifting-wf"
  job = "dev-use2-tedsand-openpowerlifting-cleanse-job"
  type = "EVENT"
  batch_size = 5
  batch_window = 60
}


# IAM groups, users, roles, and policies

iam_group_admin_name = "admin"
iam_user_admin_name = "tdouglas"

iam_role_glue_job = {
  name                    = "dev-tedsand-glue-job-role"
  description             = "Role for Glue jobs to assume"
  policy_name             = "dev-tedsand-glue-job-policy"
  policy_file             = "./policies/glue_job_policy.json"
  assume_role_policy_file = "./policies/glue_assume_role_policy.json"
}

iam_role_glue_notebook = {
  name                    = "dev-tedsand-glue-notebook-role"
  description             = "Role for Glue notebooks to assume"
  policy_name             = "dev-tedsand-glue-notebook-policy"
  policy_file             = "./policies/glue_notebook_policy.json"
  assume_role_policy_file = "./policies/glue_assume_role_policy.json"
}

iam_role_lambda = {
  name                    = "dev-tedsand-lambda-role"
  description             = "Role for Lambda functions"
  assume_role_policy_file = "./policies/lambda_assume_role_policy.json"
  sns_policy_file         = "./policies/publish_to_sns_topic_policy.json"
}

iam_role_eventbridge_start_workflow = {
  name                    = "dev-tedsand-eb-start-workflow-role"
  description             = "Role for Eventbridge to start Glue workflows"
  policy_name             = "dev-tedsand-eb-start-workflow-policy"
  policy_file             = "./policies/eventbridge_glue_policy.json"
  assume_role_policy_file = "./policies/eventbridge_assume_role_policy.json"
}

iam_policy_lambda_results_publish_to_sns_name = "dev-use2-tedsand-lambda-results-publish-to-sns-policy"

# Lambda functions

lambda_openpowerlifting_src = "../python/lambda/lambda_ingest_openpowerlifting.py"
lambda_openpowerlifting_build = "../build/lambda_ingest_openpowerlifting.zip"
lambda_openpowerlifting_s3_key = "lambda/lambda_ingest_openpowerlifting.zip"
lambda_openpowerlifting_handler = "lambda_ingest_openpowerlifting.lambda_handler"

lambda_layer_utils_name = "lambda_utils"
lambda_layer_utils_src = "../python/layers/utils"
lambda_layer_utils_build = "../build/lambda_utils.zip"
lambda_layer_utils_s3_key = "libs/lambda_utils.zip"

lambda_function_openpowerlifting = {
  function_name   = "dev-use2-tedsand-openpowerlifting-ingest-lambda"
  runtime         = "python3.13"
  layers          = ["arn:aws:lambda:us-east-2:336392948345:layer:AWSSDKPandas-Python313:1",]
  memory_size     = 3008
  publish         = false
  timeout         = 60
  url             = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
}


# S3 buckets

s3_bucket_athena = {
  bucket                  = "dev-use2-tedsand-athena-results-s3"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  bucket_versioning_status = "Suspended"
}

s3_bucket_raw_data = {
  bucket                  = "dev-use2-tedsand-raw-data-s3"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  bucket_versioning_status = "Suspended"
}

s3_bucket_iceberg = {
  bucket                  = "dev-use2-tedsand-iceberg-s3"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  bucket_versioning_status = "Suspended"
}

s3_bucket_python = {
  bucket                  = "dev-use2-tedsand-python-s3"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  bucket_versioning_status = "Enabled"
}

s3_bucket_terraform = {
  bucket                  = "dev-use2-tedsand-terraform-s3"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  bucket_versioning_status = "Enabled"
}

s3_bucket_logs = {
  bucket                  = "dev-use2-tedsand-logs-s3"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
  bucket_versioning_status = "Enabled"
}


# SNS topics

sns_topic_lambda_results = {
  name         = "dev-use2-tedsand-lambda-results-sns"
  display_name = "AWS Sandbox SNS"
  policy_file  = "./policies/sns_topic_policy.json"
}
