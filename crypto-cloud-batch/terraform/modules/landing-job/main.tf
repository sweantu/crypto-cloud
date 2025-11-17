
# --- S3 bucket for Glue scripts ---
resource "aws_s3_bucket" "glue_scripts" {
  bucket        = "${var.project_prefix}-${var.glue_scripts_bucket_name}"
  force_destroy = true

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

# --- IAM Role for Glue ---
resource "aws_iam_role" "glue_job_role" {
  name = "${var.project_prefix}-glue-job-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# --- IAM Policy for Glue to access S3, Glue, Logs ---
resource "aws_iam_role_policy" "glue_policy" {
  name = "${var.project_prefix}-glue-policy"
  role = aws_iam_role.glue_job_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:*", "logs:*", "glue:*"]
        Resource = "*"
      }
    ]
  })
}

# --- Glue Job definition ---
resource "aws_glue_job" "landing_job" {
  name     = "${var.project_prefix}-landing-job"
  role_arn = aws_iam_role.glue_job_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_scripts.bucket}/job/landing_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                      = "python"
    "--enable-glue-datacatalog"           = "true"
    "--enable-continuous-cloudwatch-log"  = "true"
    "--TempDir"                           = "s3://${aws_s3_bucket.glue_scripts.bucket}/temp/"
    "--symbol"                            = "ADAUSDT"
    "--landing_date"                      = "2025-09-27"
    "--project_prefix"                    = var.project_prefix
    "--data_lake_bucket_name"             = var.data_lake_bucket_name
    "--data_lake_iceberg_lock_table_name" = var.data_lake_iceberg_lock_table_name
  }

  glue_version      = "5.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 10
  max_retries       = 0
}
