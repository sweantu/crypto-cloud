variable "region" {
  type = string
}

variable "profile" {
  type = string
}

variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "az_count" {
  type = number
}

variable "clickhouse_db" {
  type      = string
  sensitive = true
}

variable "clickhouse_user" {
  type      = string
  sensitive = true
}

variable "clickhouse_password" {
  type      = string
  sensitive = true
}

variable "clickhouse_instance_type" {
  type = string
}

variable "clickhouse_ami_id" {
  type = string
}

variable "key_name" {
  type      = string
  sensitive = true
}
