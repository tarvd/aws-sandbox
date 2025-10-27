resource "aws_iam_group" "admin" {
  name = "admin"
}

resource "aws_iam_user" "tdouglas" {
  name = "tdouglas"

  tags = merge(
    local.tags,
    { name = "tdouglas-iam-user" }
  )
}

resource "aws_iam_role" "glue_role" {
  name = "dev-tedsand-glue-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "glue_job_policy" {
  name        = "dev-tedsand-glue-job-policy"
  description = "Policy for Glue job to access S3 bucket and Glue Data Catalog"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "glue:*"                     # Or restrict to create/update/get tables/databases if you want
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.python.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.python.bucket}/glue/*",
          "arn:aws:s3:::${aws_s3_bucket.raw_data.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.raw_data.bucket}/*",
          "arn:aws:s3:::${aws_s3_bucket.cleansed_data.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.cleansed_data.bucket}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_job_attach" {
  role       = aws_iam_role.glue_role.name
  policy_arn = aws_iam_policy.glue_job_policy.arn
}
