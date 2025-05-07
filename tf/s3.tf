resource "aws_s3_bucket" "s3_athena" {
  bucket = "ted-sand-dev-s3-use2-athena"

  tags = merge(
    local.tags,
    {name = "athena-s3"}
  )
}

resource "aws_s3_bucket" "s3_data" {
  bucket = "ted-sand-dev-s3-use2-data"

  tags = merge(
    local.tags,
    {name = "data-s3"}
  )
}

resource "aws_s3_bucket" "s3_lambda" {
  bucket = "ted-sand-dev-s3-use2-lambda"

  tags = merge(
    local.tags,
    {name = "lambda-s3"}
  )
}
