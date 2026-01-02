data "archive_file" "utils_zip" {
  type        = "zip"
  source_dir  = var.py_utils_src
  output_path = var.py_utils_build
}

resource "aws_s3_object" "utils_zip" {
  bucket = aws_s3_bucket.python.id
  key    = var.py_utils_s3_key

  source = var.py_utils_build
  etag   = filemd5(var.py_utils_build)
}

resource "aws_s3_object" "openpowerlifting_cleanse_job" {
  bucket = aws_s3_bucket.python.id
  key    = var.glue_job_openpowerlifting_cleanse.s3_key

  source = var.glue_job_openpowerlifting_cleanse.script
  etag   = filemd5(var.glue_job_openpowerlifting_cleanse.script)
}

resource "aws_glue_job" "openpowerlifting_cleanse_job" {
  name              = var.glue_job_openpowerlifting_cleanse.name
  description       = var.glue_job_openpowerlifting_cleanse.description
  glue_version      = var.glue_job_openpowerlifting_cleanse.glue_version
  max_retries       = var.glue_job_openpowerlifting_cleanse.max_retries
  timeout           = var.glue_job_openpowerlifting_cleanse.timeout
  number_of_workers = var.glue_job_openpowerlifting_cleanse.number_of_workers
  worker_type       = var.glue_job_openpowerlifting_cleanse.worker_type
  execution_class   = var.glue_job_openpowerlifting_cleanse.execution_class
  default_arguments = merge(
    var.glue_job_openpowerlifting_cleanse.default_arguments,
    {
      "--sns_topic_arn" = aws_sns_topic.lambda_results.arn,
      "--extra-py-files" = "s3://${aws_s3_bucket.python.id}/${aws_s3_object.utils_zip.key}"
    }
  )

  command {
    name            = var.glue_job_openpowerlifting_cleanse.command
    script_location = "s3://${aws_s3_object.openpowerlifting_cleanse_job.bucket}/${aws_s3_object.openpowerlifting_cleanse_job.key}"
  }

  role_arn          = aws_iam_role.glue_job_role.arn
}

resource "aws_glue_workflow" "openpowerlifting" {
  name                = var.glue_workflow_openpowerlifting.name
  description         = var.glue_workflow_openpowerlifting.description
  max_concurrent_runs = var.glue_workflow_openpowerlifting.max_concurrent_runs
}

resource "aws_glue_trigger" "openpowerlifting" {
  name          = var.glue_trigger_openpowerlifting_cleanse.name
  workflow_name = var.glue_trigger_openpowerlifting_cleanse.workflow
  type          = var.glue_trigger_openpowerlifting_cleanse.type

  actions {
    job_name = var.glue_trigger_openpowerlifting_cleanse.job
  }

  event_batching_condition {
    batch_size    = var.glue_trigger_openpowerlifting_cleanse.batch_size
    batch_window  = var.glue_trigger_openpowerlifting_cleanse.batch_window
  }

}