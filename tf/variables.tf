
# Top level vars

variable "aws_account_id" {
  type    = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "AWS Account ID must be a 12-digit number"
  }
}

variable "sns_email" {
  type    = string
}

variable "env" {
  type    = string
  default = "dev"
}

variable "region" {
  type    = string 
  default = "us-east-2"
}

variable "region_short_code" {
  type    = string 
  default = "use2"
}

variable "project" {
  type    = string 
  default = "tedsand"
}


# Athena workgroups

variable "athena_workgroup_primary" {
  type = object({
    name                               = string
    enforce_workgroup_configuration    = bool
    publish_cloudwatch_metrics_enabled = bool
    encryption_option                  = string
    acl_option                         = string
  })
}

variable "athena_workgroup_dbt" {
  type = object({
    name                               = string
    enforce_workgroup_configuration    = bool
    publish_cloudwatch_metrics_enabled = bool
    encryption_option                  = string
    acl_option                         = string
  })
}


# Eventbridge rules and targets

variable "eventbridge_rule_daily" {
  type = object({
    name                = string
    description         = string
    schedule_expression = string
    target_id           = string
  })
}

variable "eventbridge_rule_new_data_openpowerlifting" {
  type = object({
    name = string
    description = string
    s3_bucket = string
    s3_prefix = string
    target_id = string
    sns_target_id = string
  })
}


# Glue catalog databases and tables

variable "glue_database_raw" {
  type = object({
    name = string
    default_permissions = list(string)
    lf_principal = string
  })
}

variable "glue_database_cleansed" {
  type = object({
    name = string
    default_permissions = list(string)
    lf_principal = string
  })
}

variable "glue_database_metadata" {
  type = object({
    name = string
    default_permissions = list(string)
    lf_principal = string
  })
}

variable "glue_database_dbt" {
  type = object({
    name = string
    default_permissions = list(string)
    lf_principal = string
  })
}

variable "glue_table_openpowerlifting_raw" {
  type = object({
    name = string
    database = string
    table_type = string
    classification = string
    skip_header_line_count = string
    s3_prefix = string
    input_format = string
    output_format = string
    compressed = bool
    serialization_library = string
    separation_char = string
    column_list = list(string)
    partition_column_list = list(string)
  })
}


# Glue ETL jobs, workflows, and triggers

variable "py_utils_src" {
  type    = string
}

variable "py_utils_build" {
  type    = string
  validation {
    condition     = can(regex("\\.zip$", var.py_utils_build))
    error_message = "Value must be a .zip file"
  }
}

variable "py_utils_s3_key" {
  type    = string
  validation {
    condition     = can(regex("\\.zip$", var.py_utils_s3_key))
    error_message = "Value must be a .zip file"
  }
}

variable "glue_job_openpowerlifting_cleanse" {
  type = object({
    name              = string
    description       = string
    glue_version      = string
    max_retries       = number
    timeout           = number
    number_of_workers = number
    worker_type       = string
    execution_class   = string
    command           = string
    script            = string
    s3_key            = string
    default_arguments = map(string)
  })
}

variable "glue_workflow_openpowerlifting" {
  type = object({
    name = string
    description = string
    max_concurrent_runs = number
  })
}

variable "glue_trigger_openpowerlifting_cleanse" {
  type = object({
    name = string
    workflow = string
    job = string
    type = string
    batch_size = number
    batch_window = number
  })
}


# IAM groups, users, roles, and policies

variable "iam_group_admin_name" {
  type = string
}

variable "iam_user_admin_name" {
  type = string
}

variable "iam_role_glue_job" {
  type = object({
    name                    = string
    description             = string
    policy_name             = string
    policy_file             = string
    assume_role_policy_file = string
  })
}

variable "iam_role_glue_notebook" {
  type = object({
    name                    = string
    description             = string
    policy_name             = string
    policy_file             = string
    assume_role_policy_file = string
  })
}

variable "iam_role_lambda" {
  type = object({
    name                    = string
    description             = string
    assume_role_policy_file = string
    sns_policy_file         = string
  })
}

variable "iam_role_eventbridge_start_workflow" {
  type = object({
    name                    = string
    description             = string
    policy_name             = string
    policy_file             = string
    assume_role_policy_file = string
  })
}

variable "iam_policy_lambda_results_publish_to_sns_name" {
  type = string
}

# Lambda functions

variable "lambda_openpowerlifting_src" {
  type    = string
  validation {
    condition     = can(regex("\\.py$", var.lambda_openpowerlifting_src))
    error_message = "Value must be a .py file"
  }
}

variable "lambda_openpowerlifting_build" {
  type    = string
  validation {
    condition     = can(regex("\\.zip$", var.lambda_openpowerlifting_build))
    error_message = "Value must be a .zip file"
  }
}

variable "lambda_openpowerlifting_s3_key" {
  type    = string
  validation {
    condition     = can(regex("\\.zip$", var.lambda_openpowerlifting_s3_key))
    error_message = "Value must be a .zip file"
  }
}

variable "lambda_openpowerlifting_handler" {
  type    = string
  validation {
    condition     = can(regex("\\.lambda_handler$", var.lambda_openpowerlifting_handler))
    error_message = "Value must be a lambda handler"
  }
}

variable "lambda_layer_utils_name" {
  type    = string
}

variable "lambda_layer_utils_src" {
  type    = string
}

variable "lambda_layer_utils_build" {
  type    = string
  validation {
    condition     = can(regex("\\.zip$", var.lambda_layer_utils_build))
    error_message = "Value must be a .zip file"
  }
}

variable "lambda_layer_utils_s3_key" {
  type    = string
  validation {
    condition     = can(regex("\\.zip$", var.lambda_layer_utils_s3_key))
    error_message = "Value must be a .zip file"
  }
}

variable "lambda_function_openpowerlifting" {
  type = object({
    function_name    = string
    runtime          = string
    memory_size      = number
    publish          = bool
    timeout          = number
    url              = string
  })
}


# S3 buckets

variable "s3_bucket_athena" {
  type = object({
    bucket                  = string
    block_public_acls       = bool
    block_public_policy     = bool
    ignore_public_acls      = bool
    restrict_public_buckets = bool
    bucket_versioning_status = string
  })
}

variable "s3_bucket_raw_data" {
  type = object({
    bucket                  = string
    block_public_acls       = bool
    block_public_policy     = bool
    ignore_public_acls      = bool
    restrict_public_buckets = bool
    bucket_versioning_status = string
  })
}

variable "s3_bucket_iceberg" {
  type = object({
    bucket                  = string
    block_public_acls       = bool
    block_public_policy     = bool
    ignore_public_acls      = bool
    restrict_public_buckets = bool
    bucket_versioning_status = string
  })
}

variable "s3_bucket_python" {
  type = object({
    bucket                  = string
    block_public_acls       = bool
    block_public_policy     = bool
    ignore_public_acls      = bool
    restrict_public_buckets = bool
    bucket_versioning_status = string
  })
}

variable "s3_bucket_terraform" {
  type = object({
    bucket                  = string
    block_public_acls       = bool
    block_public_policy     = bool
    ignore_public_acls      = bool
    restrict_public_buckets = bool
    bucket_versioning_status = string
  })
}

variable "s3_bucket_logs" {
  type = object({
    bucket                  = string
    block_public_acls       = bool
    block_public_policy     = bool
    ignore_public_acls      = bool
    restrict_public_buckets = bool
    bucket_versioning_status = string
  })
}


# SNS topics

variable "sns_topic_lambda_results" {
  type = object({
    name         = string
    display_name = string
    policy_file  = string
  })
}
