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
