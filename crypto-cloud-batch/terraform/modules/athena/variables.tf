variable "project_prefix" {}
variable "data_lake_bucket_name" {}

variable "project" {
  description = "Project name for tagging resources"
  type        = string
}

variable "environment" {
  description = "Environment name for tagging resources"
  type        = string
}

variable "grafana_ecs_task_execution_role_name" {
  description = "IAM Role name for Grafana ECS Task"
  type        = string
}
