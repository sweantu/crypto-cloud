output "data_lake_bucket_name" {
  value = module.data-lake.data_lake_bucket_name
}

output "data_lake_bucket_arn" {
  value = module.data-lake.data_lake_bucket_arn
}

output "data_lake_iceberg_lock_table_name" {
  value = module.data-lake.data_lake_iceberg_lock_table_name
}

output "glue_scripts_bucket_name" {
  value = module.landing-job.glue_scripts_bucket_name
}

output "glue_scripts_bucket_arn" {
  value = module.landing-job.glue_scripts_bucket_arn
}

output "glue_job_role_arn" {
  value = module.landing-job.glue_job_role_arn
}

output "landing_job_name" {
  value = module.landing-job.landing_job_name
}

output "transform_job_name" {
  value = module.transform-job.transform_job_name
}

output "transform_job_name_pattern_two" {
  value = module.transform-job-pattern-two.transform_job_name_pattern_two
}