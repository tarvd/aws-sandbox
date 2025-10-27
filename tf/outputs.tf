output "lambda_function_name" {
  value = aws_lambda_function.openpowerlifting_ingest.function_name
}

output "athena_query_results_bucket" {
  value = aws_s3_bucket.athena_results.bucket
}
