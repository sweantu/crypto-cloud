locals {
  glue_default_arguments = {
    "--job-language"                     = "python"
    "--enable-glue-datacatalog"          = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                          = "s3://${var.glue_scripts_directory}/temp/"
  }
}

resource "aws_glue_job" "jobs" {
  for_each = var.glue_jobs_map
  name     = each.value.name
  role_arn = aws_iam_role.glue_role.arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.glue_scripts_directory}/${each.key}.py"
    python_version  = "3"
  }

  default_arguments = merge(local.glue_default_arguments, each.value.extra_arguments)

  glue_version      = "5.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 10
  max_retries       = 0
}
