data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}


locals {
  account_id                = data.aws_caller_identity.current.account_id
  project_prefix            = "${var.project}-${var.environment}-${local.account_id}"
  project_prefix_underscore = replace(local.project_prefix, "-", "_")
  azs                       = slice(data.aws_availability_zones.available.names, 0, var.az_count)
}

module "vpc" {
  source                    = "./modules/vpc"
  vpc_cidr                  = var.vpc_cidr
  azs                       = local.azs
  project_prefix            = local.project_prefix
  project_prefix_underscore = local.project_prefix_underscore
}

module "data_lake" {
  source                    = "./modules/data-lake"
  project_prefix            = local.project_prefix
  project_prefix_underscore = local.project_prefix_underscore
}

module "clickhouse" {
  source                    = "./modules/clickhouse"
  vpc_id                    = module.vpc.vpc_id
  subnet_id                 = module.vpc.public_subnet_ids[0]
  project_prefix            = local.project_prefix
  project_prefix_underscore = local.project_prefix_underscore

  clickhouse_db       = var.clickhouse_db
  clickhouse_user     = var.clickhouse_user
  clickhouse_password = var.clickhouse_password

  clickhouse_instance_type = var.clickhouse_instance_type
  clickhouse_ami_id        = var.clickhouse_ami_id

  key_name = var.key_name
}

module "athena" {
  source = "./modules/athena"

  project_prefix        = local.project_prefix
  data_lake_bucket_name = module.data_lake.data_lake_bucket_name
  athena_output_prefix  = "athena_output/"
}

module "glue" {
  source = "./modules/glue"

  project_prefix            = local.project_prefix
  project_prefix_underscore = local.project_prefix_underscore
  data_lake_bucket_name     = module.data_lake.data_lake_bucket_name
  iceberg_lock_table_name   = module.data_lake.iceberg_lock_table_name

}
