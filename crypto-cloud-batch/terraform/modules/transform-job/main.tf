# --- Glue Job definition ---
resource "aws_glue_job" "transform_job" {
  name     = "${var.project_prefix}-transform-job"
  role_arn = var.glue_job_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_scripts_bucket_name}/job/transform_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                      = "python"
    "--enable-glue-datacatalog"           = "true"
    "--enable-continuous-cloudwatch-log"  = "true"
    "--TempDir"                           = "s3://${var.glue_scripts_bucket_name}/temp/"
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
