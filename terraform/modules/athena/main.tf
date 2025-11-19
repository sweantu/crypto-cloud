resource "aws_athena_workgroup" "athena_wg" {
  name  = "${var.project_prefix}-athena-wg"
  state = "ENABLED"
  lifecycle {
    prevent_destroy = true
    ignore_changes  = [state, configuration]
  }

  configuration {
    enforce_workgroup_configuration = true

    result_configuration {
      output_location = "s3://${var.data_lake_bucket_name}/${var.athena_output_prefix}"
    }
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
      prefix = var.athena_output_prefix
    }

    expiration {
      days = 7
    }
  }
}
