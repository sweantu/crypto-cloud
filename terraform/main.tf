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

module "ecr" {
  source = "./modules/ecr"

  project_prefix = local.project_prefix
}

module "ecs" {
  source = "./modules/ecs"

  project_prefix = local.project_prefix
}

module "airflow" {
  source = "./modules/airflow"

  project_prefix                 = local.project_prefix
  region                         = var.region
  vpc_id                         = module.vpc.vpc_id
  public_subnet_ids              = module.vpc.public_subnet_ids
  airflow_db_username            = var.airflow_db_username
  airflow_db_password            = var.airflow_db_password
  airflow_db_name                = var.airflow_db_name
  airflow_fernet_key             = var.airflow_fernet_key
  ecs_execution_role_arn         = module.ecs.ecs_execution_role_arn
  ecs_cluster_id                 = module.ecs.ecs_cluster_id
  airflow_repo_url               = module.ecr.airflow_repo_url
  airflow_admin_username         = var.airflow_admin_username
  airflow_admin_password         = var.airflow_admin_password
  airflow_admin_email            = var.airflow_admin_email
  landing_job_name               = module.glue.landing_job_name
  transform_job_name             = module.glue.transform_job_name
  transform_job_pattern_two_name = module.glue.transform_job_pattern_two_name
}

module "kinesis" {
  source = "./modules/kinesis"

  project_prefix = local.project_prefix
}

module "scripts" {
  source = "./modules/scripts"

  project_prefix = local.project_prefix
}

module "flink" {
  source = "./modules/flink"

  project_prefix = local.project_prefix
  region         = var.region
  stream_arns = tomap({
    "ExampleInputStream"  = "arn:aws:kinesis:${var.region}:${local.account_id}:stream/${local.project_prefix}-aggtrades-stream",
    "ExampleOutputStream" = "arn:aws:kinesis:${var.region}:${local.account_id}:stream/${local.project_prefix}-engulfings-stream"
  })
  scripts_bucket_arn = module.scripts.flink_scripts_bucket_arn
  data_lake_bucket   = module.data_lake.data_lake_bucket_name
}

module "lambda" {
  source = "./modules/lambda"

  project_prefix      = local.project_prefix
  kinesis_stream_name = "${local.project_prefix}-aggtrades-stream"
  region              = var.region
}

module "producers" {
  source = "./modules/producers"

  project_prefix              = local.project_prefix
  region                      = var.region
  vpc_id                      = module.vpc.vpc_id
  public_subnet_ids           = module.vpc.public_subnet_ids
  ecs_execution_role_arn      = module.ecs.ecs_execution_role_arn
  ecs_cluster_id              = module.ecs.ecs_cluster_id
  aggtrades_producer_repo_url = module.ecr.aggtrades_producer_repo_url
  aggtrades_stream_name       = "${local.project_prefix}-aggtrades-stream"
  default_symbols             = "[\"ADAUSDT\",\"SUIUSDT\"]"
  default_landing_dates       = "[\"2025-09-27\",\"2025-09-28\"]"
}
