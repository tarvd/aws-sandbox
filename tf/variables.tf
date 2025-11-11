
# Top level vars

variable "aws_account_id" {
  type    = string
  default = "820242901733"
  validation {
    condition     = can(regex("^[0-9]{12}$", var.aws_account_id))
    error_message = "AWS Account ID must be a 12-digit number"
  }
}

variable "env" {
  type    = string
  default = "dev"
}


# Athena vars

variable "athena_workgroup_primary" {
  type = object({
    name = string
    enforce_workgroup_configuration = bool
    publish_cloudwatch_metrics_enabled = bool
    encryption_option = string
  })
}

variable "lambda_openpowerlifting_filename" {
  type    = string
  default = "../python/lambda/lambda_ingest_openpowerlifting.zip"
  validation {
    condition     = can(regex("\\.zip$", var.lambda_openpowerlifting_filename))
    error_message = "Filename must be a .zip file"
  }

}

variable "lambda_openpowerlifting_handler" {
  type    = string
  default = "lambda_ingest_openpowerlifting.lambda_handler"
  validation {
    condition     = can(regex("\\.lambda_handler$", var.lambda_openpowerlifting_handler))
    error_message = "Function must be a lambda handler"
  }
}
