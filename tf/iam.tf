resource "aws_iam_group" "admin" {
  name = var.iam_group_admin_name
}

resource "aws_iam_user" "tdouglas" {
  name = var.iam_user_admin_name

  tags = merge(
    local.tags,
    { name = "tdouglas-iam-user" }
  )
}

resource "aws_iam_role" "glue_job_role" {
  name = var.iam_role_glue_job.name
  description = var.iam_role_glue_job.description
  assume_role_policy = "${file("./policies/glue_assume_role_policy.json")}"
}

resource "aws_iam_role" "glue_notebook_role" {
  name = var.iam_role_glue_notebook.name 
  description = var.iam_role_glue_notebook.description
  assume_role_policy = "${file("./policies/glue_assume_role_policy.json")}"
}

resource "aws_iam_policy" "glue_job_policy" {
  name        = var.iam_policy_glue_job.name
  description = var.iam_policy_glue_job.description
  policy = templatefile(
    "./policies/glue_job_policy.json.tpl",
    {
      python_s3_bucket = "${aws_s3_bucket.python.bucket}"
      raw_data_s3_bucket = "${aws_s3_bucket.raw_data.bucket}"
      iceberg_s3_bucket = "${aws_s3_bucket.iceberg.bucket}"
    })
}

resource "aws_iam_role_policy_attachment" "glue_job_attach" {
  role       = aws_iam_role.glue_job_role.name
  policy_arn = aws_iam_policy.glue_job_policy.arn
}

resource "aws_iam_policy" "glue_notebook_policy" {
  name        = var.iam_policy_glue_notebook.name
  description = var.iam_policy_glue_notebook.description

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

data "aws_iam_policy" "AmazonS3FullAccess" {
  arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

data "aws_iam_policy" "AWSLambdaBasicExecutionRole" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "lambda_role" {
  name        = var.iam_role_lambda.name
  description = var.iam_role_lambda.description

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda-role-s3-policy-attach" {
  role       = "${aws_iam_role.lambda_role.name}"
  policy_arn = "${data.aws_iam_policy.AmazonS3FullAccess.arn}"
}

resource "aws_iam_role_policy_attachment" "lambda-role-lambda-policy-attach" {
  role       = "${aws_iam_role.lambda_role.name}"
  policy_arn = "${data.aws_iam_policy.AWSLambdaBasicExecutionRole.arn}"
}

resource "aws_iam_role" "eb_start_workflow" {
  name = var.iam_role_eventbridge_start_workflow.name 
  description = var.iam_role_eventbridge_start_workflow.description
  path = "/service-role/"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Sid       = "TrustEventBridgeService"
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = var.aws_account_id
          "aws:SourceArn"     = aws_cloudwatch_event_rule.openpowerlifting.arn
        }
      }
      Effect    = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "eb_start_workflow" {
  name        = var.iam_policy_eventbridge_start_workflow.name 
  description = var.iam_policy_eventbridge_start_workflow.description
  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ActionsForResource",
            "Effect": "Allow",
            "Action": [
                "glue:NotifyEvent"
            ],
            "Resource": [
                "arn:aws:glue:us-east-2:820242901733:workflow/dev-use2-tedsand-openpowerlifting-wf"
            ]
        }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eb_start_workflow" {
  role       = "${aws_iam_role.eb_start_workflow.name}"
  policy_arn = "${aws_iam_policy.eb_start_workflow.arn}"
}
