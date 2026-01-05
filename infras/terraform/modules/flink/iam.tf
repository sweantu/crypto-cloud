resource "aws_iam_role" "flink_role" {
  name = "${var.project_prefix}-flink-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "kinesisanalytics.amazonaws.com" },
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "flink_policy" {
  name = "${var.project_prefix}-flink-policy"
  role = aws_iam_role.flink_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:*",
          "logs:*",
          "glue:*",
          "kinesis:*",
          "dynamodb:*"
        ],
        Resource = "*"
      }
    ]
  })
}
