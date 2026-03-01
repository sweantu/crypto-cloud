variable "aws_profile" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "data_lake_bucket" {
  type = string
}

variable "iceberg_lock_table" {
  type = string
}

variable "transform_db" {
  type = string
}

variable "airflow_db_username" {
  type = string
}

variable "airflow_db_password" {
  type      = string
  sensitive = true
}

variable "airflow_db_name" {
  type = string
}

variable "airflow_fernet_key" {
  type      = string
  sensitive = true
}

variable "airflow_admin_username" {
  type = string
}

variable "airflow_admin_password" {
  type      = string
  sensitive = true
}

variable "airflow_admin_email" {
  type = string
}

variable "clickhouse_db" {
  type = string
}

variable "clickhouse_user" {
  type = string
}

variable "clickhouse_password" {
  type      = string
  sensitive = true
}

variable "environment" {
  type = string
}

variable "grafana_admin_username" {
  type = string
}

variable "grafana_admin_password" {
  type      = string
  sensitive = true
}

variable "project" {
  type = string
}

variable "ssh_key" {
  type      = string
  sensitive = true
}
