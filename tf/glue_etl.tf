
# resource "aws_glue_job" "openpowerlifting_cleansed_ddl" {
#   name     = "dev-use2-tedsand-openpowerlifting-cleansed-ddl-job"
#   role_arn = "arn:aws:iam::${var.aws_account_id}:role/${aws_iam_role.glue_role.name}"  # your existing IAM role ARN

#   command {
#     name            = "glueetl"  # or "pythonshell" if Python script
#     script_location = "s3://${aws_s3_bucket.python.bucket}/glue/glue_ddl_openpowerlifting.py"
#   }

#   glue_version = "5.0"           # AWS Glue version, e.g. 2.0, 3.0, etc.
#   max_retries = 0
#   number_of_workers = 2
#   worker_type = "G.1X"  # If you use number_of_workers, specify worker type too
# }
