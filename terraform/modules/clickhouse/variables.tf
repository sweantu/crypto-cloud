variable "project_prefix" {
  type = string
}

variable "project_prefix_underscore" {
  type = string
}

variable "vpc_id" {
  type = string
}
variable "subnet_id" {
  type = string
}

variable "key_name" {
  type      = string
  sensitive = true
}

variable "clickhouse_instance_type" {
  type = string
}

variable "clickhouse_ami_id" {
  type = string
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
