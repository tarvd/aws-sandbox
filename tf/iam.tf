resource "aws_iam_group" "admin" {
  name = "admin"
}

resource "aws_iam_user" "tdouglas" {
  name = "tdouglas"

  tags = {
    org = "ted"
    product = "sand"
    env = "dev"
    name = "tdouglas-iam-user"
    AKIA356SJNLSVAPD4LW2 = "cli"
  }
}
