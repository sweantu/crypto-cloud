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

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "grafana_cluster_name" {
  value = module.grafana.grafana_cluster_name
}

output "grafana_security_group" {
  value = module.grafana.grafana_security_group
}

output "grafana_service_name" {
  value = module.grafana.grafana_service_name
}

output "athena_workgroup_name" {
  value = module.athena.athena_workgroup_name
}

output "athena_result_path" {
  value = module.athena.athena_result_path
}

output "airflow_db_endpoint" {
  value = module.airflow.airflow_db_endpoint
}

# output "stream_name" {
#   value = module.kinesis.stream_name
# }

# output "stream_arn" {
#   value = module.kinesis.stream_arn
# }

# output "clickhouse_public_ip" {
#   value = module.clickhouse.clickhouse_public_ip
# }

# output "stream_names_lists" {
#   value = [for k, v in module.kinesis.stream_names : v]
# }

# output "stream_arns_list" {
#   value = [for k, v in module.kinesis.stream_arns : v]
# }
