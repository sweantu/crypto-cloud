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

output "clickhouse_instance_id" {
  value = module.clickhouse.clickhouse_instance_id
}
