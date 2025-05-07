variable "lambda_openpowerlifting_filename" {
  type    = string
  default = "../python/lambda_ingest_openpowerlifting.zip"
}

variable "lambda_openpowerlifting_handler" {
  type    = string
  default = "lambda_ingest_openpowerlifting.lambda_handler"
}

variable "aws_account_id" {
  type    = string
  default = "820242901733"
}
