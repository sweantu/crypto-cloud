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

variable "airflow_db_username" {
  type      = string
  sensitive = true
}
variable "airflow_db_password" {
  type      = string
  sensitive = true
}

variable "airflow_db_name" {
  type      = string
  sensitive = true
}

variable "airflow_fernet_key" {
  type      = string
  sensitive = true
}

variable "ecs_execution_role_arn" {
  type = string
}

variable "ecs_cluster_id" {
  type = string
}

variable "airflow_repo_url" {
  type = string
}

variable "airflow_admin_username" {
  type      = string
  sensitive = true
}

variable "airflow_admin_password" {
  type      = string
  sensitive = true
}

variable "airflow_admin_email" {
  type      = string
  sensitive = true
}

