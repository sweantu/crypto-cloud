resource "aws_athena_workgroup" "crypto_dev" {
  name  = "${var.project_prefix}-athena-wg"
  state = "ENABLED"
  lifecycle {
    prevent_destroy = true
    ignore_changes  = [state, configuration]
  }

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://${var.data_lake_bucket_name}/athena_results/"
    }
  }

  tags = {
    Name        = "${var.project_prefix}-athena-wg"
    Environment = var.environment
    Project     = var.project
  }
}

# -------------------------
# Lifecycle rule for cleaning Athena results (7 days)
# -------------------------
resource "aws_s3_bucket_lifecycle_configuration" "athena_clean" {
  bucket = var.data_lake_bucket_name

  rule {
    id     = "delete-old-athena-results"
    status = "Enabled"

    filter {
      prefix = "athena_results/"
    }

    expiration {
      days = 7
    }
  }
}

# -------------------------
# IAM Policy for Athena + Glue + S3
# -------------------------
resource "aws_iam_role_policy" "athena_policy" {
  name = "${var.project_prefix}-athena-policy"
  role = var.grafana_ecs_task_execution_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:*", "logs:*", "glue:*", "athena:*"]
        Resource = "*"
      }
    ]
  })
}
