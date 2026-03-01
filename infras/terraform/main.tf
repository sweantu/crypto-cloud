data "aws_caller_identity" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}


locals {
  account_id                = data.aws_caller_identity.current.account_id
  project_prefix            = "${var.project}-${var.environment}-${local.account_id}"
  project_prefix_underscore = replace(local.project_prefix, "-", "_")
  azs                       = slice(data.aws_availability_zones.available.names, 0, 2)
}
module "vpc" {
  source                  = "./modules/vpc"
  vpc_cidr                = "10.0.0.0/16"
  azs                     = local.azs
  vpc_name                = "${local.project_prefix}-vpc"
  igw_name                = "${local.project_prefix}-igw"
  public_subnet_names     = { for az in local.azs : az => "${local.project_prefix}-public-${az}" }
  public_route_table_name = "${local.project_prefix}-public-rt"
}


locals {
  data_lake_bucket_name   = "${local.project_prefix}-${var.data_lake_bucket}"
  iceberg_lock_table_name = "${local.project_prefix_underscore}_${var.iceberg_lock_table}"
  transform_db_name       = "${local.project_prefix_underscore}_${var.transform_db}"
}
module "data_lake" {
  source                    = "./modules/data_lake"
  bucket_name               = local.data_lake_bucket_name
  iceberg_lock_table_name   = local.iceberg_lock_table_name
  transform_db_name         = local.transform_db_name
  transform_db_location_uri = "s3a://${local.data_lake_bucket_name}/transform_zone/"
}

locals {
  aggtrades_stream_name  = "${local.project_prefix}-aggtrades-stream"
  indicators_stream_name = "${local.project_prefix}-indicators-stream"
}
module "kinesis" {
  source = "./modules/kinesis"
  streams_props_map = {
    "aggtrades-stream" = {
      name            = local.aggtrades_stream_name
      shard_count     = 1
      retention_hours = 24
    },
    "indicators-stream" = {
      name            = local.indicators_stream_name
      shard_count     = 1
      retention_hours = 24
    }
  }
}

module "clickhouse" {
  source                   = "./modules/clickhouse"
  vpc_id                   = module.vpc.vpc_id
  subnet_id                = module.vpc.public_subnet_ids[0]
  clickhouse_sg_name       = "${local.project_prefix}-clickhouse-sg"
  clickhouse_instance_name = "${local.project_prefix}-clickhouse-instance"
  clickhouse_db            = var.clickhouse_db
  clickhouse_user          = var.clickhouse_user
  clickhouse_password      = var.clickhouse_password
  clickhouse_instance_type = "t3.medium"
  clickhouse_ami_id        = "ami-0827b3068f1548bf6"
  clickhouse_volume_size   = 50
  ssh_key                  = var.ssh_key
}

locals {
  glue_jobs_directory = "${local.data_lake_bucket_name}/glue_scripts"
}
module "glue" {
  source = "./modules/glue"

  project_prefix         = local.project_prefix
  glue_scripts_directory = local.glue_jobs_directory

  glue_jobs_map = {
    "aggtrades" : {
      name = "${local.project_prefix}-aggtrades"
      extra_arguments = {
        "--extra-py-files"   = "s3://${local.glue_jobs_directory}/aggtrades_libs.zip"
        "--symbol"           = "ADAUSDT"
        "--landing_date"     = "2025-10-01"
        "--data_lake_bucket" = local.data_lake_bucket_name
      }
    }
    "klines" : {
      name = "${local.project_prefix}-klines"
      extra_arguments = {
        "--extra-py-files"     = "s3://${local.glue_jobs_directory}/klines_libs.zip"
        "--symbol"             = "ADAUSDT"
        "--landing_date"       = "2025-10-01"
        "--data_lake_bucket"   = local.data_lake_bucket_name
        "--iceberg_lock_table" = local.iceberg_lock_table_name
        "--transform_db"       = local.transform_db_name
      }
    }

    "pattern_two" : {
      name = "${local.project_prefix}-pattern-two"
      extra_arguments = {
        "--extra-py-files"     = "s3://${local.glue_jobs_directory}/pattern_two_libs.zip"
        "--symbol"             = "ADAUSDT"
        "--landing_date"       = "2025-10-01"
        "--data_lake_bucket"   = local.data_lake_bucket_name
        "--iceberg_lock_table" = local.iceberg_lock_table_name
        "--transform_db"       = local.transform_db_name
      }
    }
  }
}

module "athena" {
  source                = "./modules/athena"
  athena_workgroup_name = "${local.project_prefix}-athena-wg"
  data_lake_bucket_name = module.data_lake.data_lake_bucket_name
  athena_output_prefix  = "athena_output/"
}

module "ecr" {
  source = "./modules/ecr"

  project_prefix = local.project_prefix
  ecr_maps = {
    "airflow_repo" = {
      name = "${local.project_prefix}-airflow-repo"
    }
    "producer_repo" = {
      name = "${local.project_prefix}-producer-repo"
    }
    "consumer_repo" = {
      name = "${local.project_prefix}-consumer-repo"
    }
  }
}

module "ecs" {
  source         = "./modules/ecs"
  project_prefix = local.project_prefix
}

module "airflow" {
  source = "./modules/airflow"

  project_prefix         = local.project_prefix
  region                 = var.aws_region
  vpc_id                 = module.vpc.vpc_id
  public_subnet_ids      = module.vpc.public_subnet_ids
  airflow_db_username    = var.airflow_db_username
  airflow_db_password    = var.airflow_db_password
  airflow_db_name        = var.airflow_db_name
  airflow_fernet_key     = var.airflow_fernet_key
  ecs_execution_role_arn = module.ecs.ecs_execution_role_arn
  ecs_cluster_id         = module.ecs.ecs_cluster_id
  airflow_repo_url       = module.ecr.ecr_repository_urls["airflow_repo"]
  airflow_admin_username = var.airflow_admin_username
  airflow_admin_password = var.airflow_admin_password
  airflow_admin_email    = var.airflow_admin_email
}

module "scripts" {
  source = "./modules/scripts"

  project_prefix = local.project_prefix
}

module "flink" {
  source = "./modules/flink"

  project_prefix = local.project_prefix
  region         = var.aws_region
  stream_arns = tomap({
    "ExampleInputStream"  = module.kinesis.stream_info_map["aggtrades-stream"].arn,
    "ExampleOutputStream" = module.kinesis.stream_info_map["indicators-stream"].arn
  })
  scripts_bucket_arn = module.scripts.flink_scripts_bucket_arn
  data_lake_bucket   = module.data_lake.data_lake_bucket_name
}

# module "lambda" {
#   source = "./modules/lambda"

#   project_prefix      = local.project_prefix
#   kinesis_stream_name = module.kinesis.stream_info_map["aggtrades-stream"].name
#   region              = var.aws_region
# }

module "producers" {
  source = "./modules/producers"

  project_prefix              = local.project_prefix
  region                      = var.aws_region
  vpc_id                      = module.vpc.vpc_id
  public_subnet_ids           = module.vpc.public_subnet_ids
  ecs_execution_role_arn      = module.ecs.ecs_execution_role_arn
  ecs_cluster_id              = module.ecs.ecs_cluster_id
  aggtrades_producer_repo_url = module.ecr.ecr_repository_urls["producer_repo"]
  default_symbols             = "[\"ADAUSDT\",\"SUIUSDT\"]"
  default_landing_dates       = "[\"2025-09-27\",\"2025-09-28\"]"
}

module "grafana" {
  source = "./modules/grafana"

  project_prefix         = local.project_prefix
  region                 = var.aws_region
  vpc_id                 = module.vpc.vpc_id
  public_subnet_ids      = module.vpc.public_subnet_ids
  ecs_execution_role_arn = module.ecs.ecs_execution_role_arn
  ecs_cluster_id         = module.ecs.ecs_cluster_id
  grafana_admin_username = var.grafana_admin_username
  grafana_admin_password = var.grafana_admin_password
}


module "sqs" {
  source = "./modules/sqs"

  project_prefix = local.project_prefix
}

module "consumers" {
  source = "./modules/consumers"

  project_prefix              = local.project_prefix
  region                      = var.aws_region
  vpc_id                      = module.vpc.vpc_id
  public_subnet_ids           = module.vpc.public_subnet_ids
  ecs_execution_role_arn      = module.ecs.ecs_execution_role_arn
  ecs_cluster_id              = module.ecs.ecs_cluster_id
  ecs_cluster_name            = module.ecs.ecs_cluster_name
  aggtrades_consumer_repo_url = module.ecr.ecr_repository_urls["consumer_repo"]
  crypto_sqs_queue_url        = module.sqs.crypto_sqs_queue_url
  crypto_sqs_queue_name       = module.sqs.crypto_sqs_queue_name
}
