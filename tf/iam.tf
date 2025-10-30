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
  name = "dev-tedsand-glue-job-role"
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

resource "aws_iam_role" "glue_notebook_role" {
  name = "dev-tedsand-glue-notebook-role"
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
          "arn:aws:s3:::${aws_s3_bucket.iceberg.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.iceberg.bucket}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_job_attach" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = aws_iam_policy.glue_job_policy.arn
}

resource "aws_iam_policy" "glue_notebook_policy" {
  name        = "glue-notebook-policy"
  description = "Policy for AWS Glue notebooks to read/write S3 and access Glue resources"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # --- Glue permissions (catalog, jobs, notebooks) ---
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:CreatePartition",
          "glue:UpdatePartition",
          "glue:DeletePartition",
          "glue:GetConnection",
          "glue:GetJob",
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
          "glue:BatchStopJobRun",
          "glue:CreateSession",
          "glue:GetSession",
          "glue:GetSessions",
          "glue:StopSession",
          "glue:TagResource",
          "glue:RunStatement",
          "glue:GetStatement"
        ]
        Resource = "*"
      },

      # --- S3 access for read/write data ---
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.raw_data.bucket}",
          "arn:aws:s3:::${aws_s3_bucket.iceberg.bucket}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.raw_data.bucket}/*",
          "arn:aws:s3:::${aws_s3_bucket.iceberg.bucket}/*"
        ]
      },

      # --- CloudWatch Logs for notebook output ---
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },

      # --- EC2 networking for Glue job runtime ---
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
      },

      # --- IAM PassRole so Glue can use this role ---
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = "*"
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "glue.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_notebook_attach" {
  role       = aws_iam_role.glue_notebook_role.name
  policy_arn = aws_iam_policy.glue_notebook_policy.arn
}
