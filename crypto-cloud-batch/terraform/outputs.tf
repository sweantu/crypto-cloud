output "data_lake_bucket_name" {
  value = module.data-lake.data_lake_bucket_name
}

output "data_lake_bucket_arn" {
  value = module.data-lake.data_lake_bucket_arn
}

output "data_lake_iceberg_lock_table_name" {
  value = module.data-lake.data_lake_iceberg_lock_table_name
}
