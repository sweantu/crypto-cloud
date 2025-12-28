resource "aws_glue_job" "transform_job" {
  name     = "${var.project_prefix}-transform-job"
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_scripts.bucket}/transform/klines.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-glue-datacatalog"          = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${aws_s3_bucket.glue_scripts.bucket}/temp/"
    "--extra-py-files"                   = "s3://${aws_s3_bucket.glue_scripts.bucket}/build/glue_job_libs/extra.zip"
    "--symbol"                           = "ADAUSDT"
    "--landing_date"                     = "2025-10-01"
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
