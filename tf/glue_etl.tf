resource "aws_glue_job" "openpowerlifting_cleanse_job" {
  name              = var.glue_job_openpowerlifting_cleanse.name
  description       = var.glue_job_openpowerlifting_cleanse.description
  role_arn          = aws_iam_role.glue_job_role.arn
  glue_version      = var.glue_job_openpowerlifting_cleanse.glue_version
  max_retries       = var.glue_job_openpowerlifting_cleanse.max_retries
  timeout           = var.glue_job_openpowerlifting_cleanse.timeout
  number_of_workers = var.glue_job_openpowerlifting_cleanse.number_of_workers
  worker_type       = var.glue_job_openpowerlifting_cleanse.worker_type
  execution_class   = var.glue_job_openpowerlifting_cleanse.execution_class

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.python.bucket}/${var.glue_job_openpowerlifting_cleanse.script_path}"
  }

  default_arguments = var.glue_job_openpowerlifting_cleanse.default_arguments
}

resource "aws_glue_workflow" "openpowerlifting" {
  name = var.glue_workflow_openpowerlifting.name
  description = var.glue_workflow_openpowerlifting.description
  max_concurrent_runs = var.glue_workflow_openpowerlifting.max_concurrent_runs
}

resource "aws_glue_trigger" "openpowerlifting" {
  name          = var.glue_trigger_openpowerlifting_cleanse.name
  type          = var.glue_trigger_openpowerlifting_cleanse.type
  workflow_name = aws_glue_workflow.openpowerlifting.name

  actions {
    job_name = aws_glue_job.openpowerlifting_cleanse_job.name
  }

  event_batching_condition {
    batch_size    = var.glue_trigger_openpowerlifting_cleanse.batch_size
    batch_window  = var.glue_trigger_openpowerlifting_cleanse.batch_window
  }

}