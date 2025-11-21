resource "aws_glue_job" "transform_job_pattern_two" {
  name     = "${var.project_prefix}-transform-job-pattern-two"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_scripts.bucket}/transform_job_pattern_two/main.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-glue-datacatalog"          = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.glue_scripts.bucket}/temp/"
    "--symbol"                           = "ADAUSDT"
    "--landing_date"                     = "2025-09-27"
    "--project_prefix_underscore"        = var.project_prefix_underscore
    "--data_lake_bucket"                 = var.data_lake_bucket_name
    "--iceberg_lock_table"               = var.iceberg_lock_table_name
  }

  glue_version      = "5.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 10
  max_retries       = 0
}
