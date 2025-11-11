resource "aws_glue_job" "openpowerlifting_cleanse_job" {
  name     = "dev-use2-tedsand-openpowerlifting-cleanse-job"
  description       = "Job to source data from Openpowerlifting Raw Data to Iceberg Cleansed Table"
  role_arn          = aws_iam_role.glue_job_role.arn
  glue_version      = "5.0"
  max_retries       = 0
  timeout           = 30
  number_of_workers = 4
  worker_type       = "G.1X"
  execution_class   = "STANDARD"

  command {
    name            = "glueetl"  # or "pythonshell" if Python script
    script_location = "s3://${aws_s3_bucket.python.bucket}/glue/openpowerlifting_cleanse_job.py"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--continuous-log-logGroup"          = "/aws-glue/jobs"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-continuous-log-filter"     = "true"
    "--enable-auto-scaling"              = "false"
    "--conf"                             = "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog --conf spark.sql.catalog.glue_catalog.warehouse=s3://dev-use2-tedsand-iceberg-s3/warehouse/ --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO"
    "--datalake-formats"                 = "iceberg"
    "--job-bookmark-option"              = "job-bookmark-disable"
    "--TempDir"                          = "s3://aws-glue-assets-${var.aws_account_id}-us-east-2/temp/"
    "--enable-glue-datacatalog"          = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.logs.id}/spark-ui/"
  }

}

resource "aws_glue_workflow" "openpowerlifting" {
  name = "dev-use2-tedsand-openpowerlifting-wf"
  description = "Glue workflow to process Openpowerlifting.org data"
  max_concurrent_runs = 1
}

resource "aws_glue_trigger" "openpowerlifting" {
  name = "dev-use2-tedsand-openpowerlifting-cleanse-tr"
  type = "EVENT"
  workflow_name = aws_glue_workflow.openpowerlifting.name
  actions {
    job_name = aws_glue_job.openpowerlifting_cleanse_job.name
  }
}