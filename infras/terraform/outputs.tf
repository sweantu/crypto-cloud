output "availability_zones" {
  value = local.azs
}

output "account_id" {
  value = local.account_id
}

output "project_prefix" {
  value = local.project_prefix
}

output "project_prefix_underscore" {
  value = local.project_prefix_underscore
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value = module.vpc.public_subnet_ids
}

output "data_lake_bucket_name" {
  value = local.data_lake_bucket_name
}

output "transform_db_name" {
  value = local.transform_db_name
}

output "iceberg_lock_table_name" {
  value = local.iceberg_lock_table_name
}

output "stream_info_map" {
  value = module.kinesis.stream_info_map
}

output "clickhouse_instance_id" {
  value = module.clickhouse.clickhouse_instance_id
}

output "glue_scripts_directory" {
  value = local.glue_jobs_directory
}

output "glue_jobs_names" {
  value = module.glue.glue_jobs_names
}

output "ecr_repository_urls" {
  value = module.ecr.ecr_repository_urls
}

output "airflow_db_endpoint" {
  value = module.airflow.airflow_db_endpoint
}

output "airflow_db_identifier" {
  value = module.airflow.airflow_db_identifier
}

output "airflow_ecs_service_name" {
  value = module.airflow.airflow_ecs_service_name
}


output "flink_scripts_bucket_name" {
  value = module.scripts.flink_scripts_bucket_name
}

# output "lambda_role_arn" {
#   value = module.lambda.lambda_role_arn
# }

# output "aggtrades_producer_lambda_name" {
#   value = module.lambda.aggtrades_producer_lambda_name
# }

output "aggtrades_producer_service_name" {
  value = module.producers.aggtrades_producer_service_name
}

output "grafana_service_name" {
  value = module.grafana.grafana_service_name
}

output "crypto_sqs_queue_url" {
  value = module.sqs.crypto_sqs_queue_url
}
output "crypto_sqs_queue_arn" {
  value = module.sqs.crypto_sqs_queue_arn
}

output "crypto_sqs_dlq_url" {
  value = module.sqs.crypto_sqs_dlq_url
}
output "crypto_sqs_dlq_arn" {
  value = module.sqs.crypto_sqs_dlq_arn
}

output "athena_wg_name" {
  value = module.athena.athena_wg_name
}

output "athena_output_location" {
  value = module.athena.athena_output_location
}
