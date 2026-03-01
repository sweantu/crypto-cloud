variable "project_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "ecs_execution_role_arn" {
  type = string
}

variable "ecs_cluster_id" {
  type = string
}

variable "aggtrades_producer_repo_url" {
  type = string
}

variable "default_symbols" {
  type    = string
  default = "[\"ADAUSDT\"]"
}

variable "default_landing_dates" {
  type    = string
  default = "[\"2025-09-27\"]"
}
