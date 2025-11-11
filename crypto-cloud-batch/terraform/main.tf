data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

locals {
  account_id     = data.aws_caller_identity.current.account_id
  project_prefix = "${var.project}-${var.environment}-${local.account_id}"
  azs            = slice(data.aws_availability_zones.available.names, 0, var.az_count)
}

module "data-lake" {
  source = "./modules/data-lake"

  project                 = var.project
  environment             = var.environment
  project_prefix          = local.project_prefix
  bucket_name             = var.data_lake_bucket_name
  iceberg_lock_table_name = var.data_lake_iceberg_lock_table_name
}

module "landing-job" {
  source = "./modules/landing-job"

  project                           = var.project
  environment                       = var.environment
  project_prefix                    = local.project_prefix
  glue_scripts_bucket_name          = var.glue_scripts_bucket_name
  data_lake_bucket_name             = module.data-lake.data_lake_bucket_name
  data_lake_iceberg_lock_table_name = module.data-lake.data_lake_iceberg_lock_table_name
}

module "transform-job" {
  source = "./modules/transform-job"

  project                           = var.project
  environment                       = var.environment
  project_prefix                    = local.project_prefix
  glue_scripts_bucket_name          = module.landing-job.glue_scripts_bucket_name
  glue_job_role_arn                 = module.landing-job.glue_job_role_arn
  data_lake_bucket_name             = module.data-lake.data_lake_bucket_name
  data_lake_iceberg_lock_table_name = module.data-lake.data_lake_iceberg_lock_table_name
}

module "transform-job-pattern-two" {
  source = "./modules/transform-job-pattern-two"

  project                           = var.project
  environment                       = var.environment
  project_prefix                    = local.project_prefix
  glue_scripts_bucket_name          = module.landing-job.glue_scripts_bucket_name
  glue_job_role_arn                 = module.landing-job.glue_job_role_arn
  data_lake_bucket_name             = module.data-lake.data_lake_bucket_name
  data_lake_iceberg_lock_table_name = module.data-lake.data_lake_iceberg_lock_table_name
}

module "vpc" {
  source = "./modules/vpc"

  project        = var.project
  environment    = var.environment
  project_prefix = local.project_prefix
  vpc_cidr       = var.vpc_cidr
  azs            = local.azs
}

module "grafana" {
  source = "./modules/grafana"

  project           = var.project
  environment       = var.environment
  project_prefix    = local.project_prefix
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
}

module "athena" {
  source = "./modules/athena"

  project                              = var.project
  environment                          = var.environment
  project_prefix                       = local.project_prefix
  data_lake_bucket_name                = module.data-lake.data_lake_bucket_name
  grafana_ecs_task_execution_role_name = module.grafana.ecs_task_execution_role_name

  depends_on = [module.grafana]
}

module "python_exec" {
  source = "./modules/python_exec"

  project_prefix    = local.project_prefix
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  project           = var.project
  environment       = var.environment
}

module "airflow" {
  source = "./modules/airflow"

  project_prefix                       = local.project_prefix
  vpc_id                               = module.vpc.vpc_id
  public_subnet_ids                    = module.vpc.public_subnet_ids
  grafana_ecs_task_execution_role_name = module.grafana.ecs_task_execution_role_name
}
