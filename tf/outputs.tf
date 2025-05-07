output "lambda_function_name" {
  value = aws_lambda_function.lambda_openpowerlifting_tf.function_name
}

output "athena_query_results_bucket" {
  value = aws_s3_bucket.s3_athena.bucket
}
