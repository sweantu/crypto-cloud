output "project_prefix" {
  value = local.project_prefix
}
output "project_prefix_underscore" {
  value = local.project_prefix_underscore
}
output "availability_zones" {
  value = local.azs
}

output "account_id" {
  value = local.account_id
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "data_lake_bucket_name" {
  value = module.data_lake.data_lake_bucket_name
}

output "iceberg_lock_table_name" {
  value = module.data_lake.iceberg_lock_table_name
}

output "clickhouse_instance_id" {
  value = module.clickhouse.clickhouse_instance_id
}

output "athena_wg_name" {
  value = module.athena.athena_wg_name
}

output "athena_output_location" {
  value = module.athena.athena_output_location
}

output "glue_scripts_bucket_name" {
  value = module.glue.glue_scripts_bucket_name
}

output "landing_job_name" {
  value = module.glue.landing_job_name
}

output "transform_job_name" {
  value = module.glue.transform_job_name
}

output "transform_job_pattern_two_name" {
  value = module.glue.transform_job_pattern_two_name
}
