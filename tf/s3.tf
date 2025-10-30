resource "aws_s3_bucket" "athena_results" {
  bucket = "dev-use2-tedsand-athena-results-s3"

  tags = merge(
    local.tags,
    { name = "athena-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket                  = aws_s3_bucket.athena_results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id
  versioning_configuration {
    status = "Suspended"
  }
}

resource "aws_s3_bucket" "raw_data" {
  bucket = "dev-use2-tedsand-raw-data-s3"

  tags = merge(
    local.tags,
    { name = "data-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "raw_data" {
  bucket                  = aws_s3_bucket.raw_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = "Suspended"
  }
}

resource "aws_s3_bucket" "cleansed_data" {
  bucket = "dev-use2-tedsand-cleansed-data-s3"

  tags = merge(
    local.tags,
    { name = "cleansed-data-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "cleansed_data" {
  bucket                  = aws_s3_bucket.cleansed_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "cleansed_data" {
  bucket = aws_s3_bucket.cleansed_data.id
  versioning_configuration {
    status = "Suspended"
  }
}

resource "aws_s3_bucket" "python" {
  bucket = "dev-use2-tedsand-python-s3"

  tags = merge(
    local.tags,
    { name = "lambda-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "python" {
  bucket                  = aws_s3_bucket.python.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "python" {
  bucket = aws_s3_bucket.python.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "terraform" {
  bucket = "dev-use2-tedsand-terraform-s3"

  tags = merge(
    local.tags,
    { name = "terraform-s3" }
  )
}

resource "aws_s3_bucket_public_access_block" "terraform" {
  bucket                  = aws_s3_bucket.terraform.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "terraform" {
  bucket = aws_s3_bucket.terraform.id
  versioning_configuration {
    status = "Enabled"
  }
}
