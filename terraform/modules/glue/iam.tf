resource "aws_iam_role" "glue_role" {
  name = "${var.project_prefix}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "glue_policy" {
  name = "${var.project_prefix}-glue-policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:*", "logs:*", "glue:*", "dynamodb:*"]
        Resource = "*"
      }
    ]
  })
}
