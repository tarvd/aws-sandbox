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

resource "aws_iam_role" "glue_job_role" {
  name = "ted-sand-dev-use2-glue-job-role"
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
  name        = "glue_job_policy"
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
          "arn:aws:s3:::aws-glue-assets-820242901733-us-east-2/",
          "arn:aws:s3:::aws-glue-assets-820242901733-us-east-2/*",
          "arn:aws:s3:::ted-sand-dev-s3-use2-data",
          "arn:aws:s3:::ted-sand-dev-s3-use2-data/*",
          "arn:aws:s3:::ted-sand-dev-s3-use2-cleansed-data",
          "arn:aws:s3:::ted-sand-dev-s3-use2-cleansed-data/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_job_attach" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = aws_iam_policy.glue_job_policy.arn
}
