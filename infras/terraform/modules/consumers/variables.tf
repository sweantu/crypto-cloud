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

variable "ecs_cluster_name" {
  type = string
}

variable "aggtrades_consumer_repo_url" {
  type = string
}

variable "crypto_sqs_queue_url" {
  type = string
}

variable "crypto_sqs_queue_name" {
  type = string
}
