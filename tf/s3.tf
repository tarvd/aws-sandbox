resource "aws_s3_bucket" "athena_results" {
  bucket = var.s3_bucket_athena.bucket
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket                  = aws_s3_bucket.athena_results.id
  block_public_acls       = var.s3_bucket_athena.block_public_acls
  block_public_policy     = var.s3_bucket_athena.block_public_policy
  ignore_public_acls      = var.s3_bucket_athena.ignore_public_acls
  restrict_public_buckets = var.s3_bucket_athena.restrict_public_buckets
}

resource "aws_s3_bucket_versioning" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id
  versioning_configuration {
    status = var.s3_bucket_athena.bucket_versioning_status
  }
}

resource "aws_s3_bucket" "raw_data" {
  bucket = var.s3_bucket_raw_data.bucket
}

resource "aws_s3_bucket_public_access_block" "raw_data" {
  bucket                  = aws_s3_bucket.raw_data.id
  block_public_acls       = var.s3_bucket_raw_data.block_public_acls
  block_public_policy     = var.s3_bucket_raw_data.block_public_policy
  ignore_public_acls      = var.s3_bucket_raw_data.ignore_public_acls
  restrict_public_buckets = var.s3_bucket_raw_data.restrict_public_buckets
}

resource "aws_s3_bucket_versioning" "raw_data" {
  bucket = aws_s3_bucket.raw_data.id
  versioning_configuration {
    status = var.s3_bucket_raw_data.bucket_versioning_status
  }
}

resource "aws_s3_bucket" "iceberg" {
  bucket = var.s3_bucket_iceberg.bucket
}

resource "aws_s3_bucket_public_access_block" "iceberg" {
  bucket                  = aws_s3_bucket.iceberg.id
  block_public_acls       = var.s3_bucket_iceberg.block_public_acls
  block_public_policy     = var.s3_bucket_iceberg.block_public_policy
  ignore_public_acls      = var.s3_bucket_iceberg.ignore_public_acls
  restrict_public_buckets = var.s3_bucket_iceberg.restrict_public_buckets
}

resource "aws_s3_bucket_versioning" "iceberg" {
  bucket = aws_s3_bucket.iceberg.id
  versioning_configuration {
    status = var.s3_bucket_iceberg.bucket_versioning_status
  }
}

resource "aws_s3_bucket" "python" {
  bucket = var.s3_bucket_python.bucket
}

resource "aws_s3_bucket_public_access_block" "python" {
  bucket                  = aws_s3_bucket.python.id
  block_public_acls       = var.s3_bucket_python.block_public_acls
  block_public_policy     = var.s3_bucket_python.block_public_policy
  ignore_public_acls      = var.s3_bucket_python.ignore_public_acls
  restrict_public_buckets = var.s3_bucket_python.restrict_public_buckets
}

resource "aws_s3_bucket_versioning" "python" {
  bucket = aws_s3_bucket.python.id
  versioning_configuration {
    status = var.s3_bucket_python.bucket_versioning_status
  }
}

resource "aws_s3_bucket" "terraform" {
  bucket = var.s3_bucket_terraform.bucket
}

resource "aws_s3_bucket_public_access_block" "terraform" {
  bucket                  = aws_s3_bucket.terraform.id
  block_public_acls       = var.s3_bucket_terraform.block_public_acls
  block_public_policy     = var.s3_bucket_terraform.block_public_policy
  ignore_public_acls      = var.s3_bucket_terraform.ignore_public_acls
  restrict_public_buckets = var.s3_bucket_terraform.restrict_public_buckets
}

resource "aws_s3_bucket_versioning" "terraform" {
  bucket = aws_s3_bucket.terraform.id
  versioning_configuration {
    status = var.s3_bucket_terraform.bucket_versioning_status
  }
}

resource "aws_s3_bucket" "logs" {
  bucket = var.s3_bucket_logs.bucket
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = var.s3_bucket_logs.block_public_acls
  block_public_policy     = var.s3_bucket_logs.block_public_policy
  ignore_public_acls      = var.s3_bucket_logs.ignore_public_acls
  restrict_public_buckets = var.s3_bucket_logs.restrict_public_buckets
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = var.s3_bucket_logs.bucket_versioning_status
  }
}
