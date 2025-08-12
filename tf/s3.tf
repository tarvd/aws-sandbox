resource "aws_s3_bucket" "s3_athena" {
  bucket = "ted-sand-dev-s3-use2-athena"

  tags = merge(
    local.tags,
    { name = "athena-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "s3_athena" {
  bucket                  = aws_s3_bucket.s3_athena.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "s3_athena" {
  bucket = aws_s3_bucket.s3_athena.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "s3_data" {
  bucket = "ted-sand-dev-s3-use2-data"

  tags = merge(
    local.tags,
    { name = "data-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "s3_data" {
  bucket                  = aws_s3_bucket.s3_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "s3_data" {
  bucket = aws_s3_bucket.s3_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "s3_cleansed_data" {
  bucket = "ted-sand-dev-s3-use2-cleansed-data"

  tags = merge(
    local.tags,
    { name = "cleansed-data-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "s3_cleansed_data" {
  bucket                  = aws_s3_bucket.s3_cleansed_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "s3_cleansed_data" {
  bucket = aws_s3_bucket.s3_cleansed_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "s3_lambda" {
  bucket = "ted-sand-dev-s3-use2-lambda"

  tags = merge(
    local.tags,
    { name = "lambda-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "s3_lambda" {
  bucket                  = aws_s3_bucket.s3_lambda.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "s3_lambda" {
  bucket = aws_s3_bucket.s3_lambda.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "s3_terraform" {
  bucket = "ted-sand-dev-s3-use2-terraform"

  tags = merge(
    local.tags,
    { name = "terraform-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "s3_terraform" {
  bucket                  = aws_s3_bucket.s3_terraform.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "s3_terraform" {
  bucket = aws_s3_bucket.s3_terraform.id
  versioning_configuration {
    status = "Enabled"
  }
}
