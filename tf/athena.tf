resource "aws_athena_workgroup" "primary" {
  name = "primary"
  configuration {
    result_configuration {
      expected_bucket_owner = var.aws_account_id
      output_location = "s3://${aws_s3_bucket.s3_athena.bucket}/primary/"
      acl_configuration {
        s3_acl_option = "BUCKET_OWNER_FULL_CONTROL"
      }
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }
}
