resource "aws_athena_workgroup" "primary" {
  name = var.athena_workgroup_primary.name

  configuration {
    enforce_workgroup_configuration    = var.athena_workgroup_primary.enforce_workgroup_configuration
    publish_cloudwatch_metrics_enabled = var.athena_workgroup_primary.publish_cloudwatch_metrics_enabled

    result_configuration {
      expected_bucket_owner = var.aws_account_id
      output_location       = "s3://${aws_s3_bucket.athena_results.bucket}/${var.athena_workgroup_primary.name}/"

      encryption_configuration {
        encryption_option = var.athena_workgroup_primary.encryption_option
      }

      acl_configuration {
        s3_acl_option = var.athena_workgroup_primary.acl_option
      }
    }
  }
}
