
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
    name = string
    enforce_workgroup_configuration = bool
    publish_cloudwatch_metrics_enabled = bool
    encryption_option = string
  })
}


# Eventbridge rules and targets

variable "eventbridge_rule_daily" {
  type = object({
    name = string
    description = string
    schedule_expression = string
  })
}

variable "eventbridge_rule_new_data_openpowerlifting" {
  type = object({
    name = string
    description = string
    prefix = string
  })
}

variable "eventbridge_target_schedule_openpowerlifting_id" {
  type = string
}

variable "eventbridge_target_new_data_openpowerlifting_id" {
  type = string
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
