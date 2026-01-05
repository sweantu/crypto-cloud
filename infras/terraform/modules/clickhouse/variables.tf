variable "vpc_id" {
  type = string
}
variable "subnet_id" {
  type = string
}

variable "ssh_key" {
  type      = string
  sensitive = true
}

variable "clickhouse_sg_name" {
  type = string
}
variable "clickhouse_instance_name" {
  type = string
}

variable "clickhouse_instance_type" {
  type = string
}

variable "clickhouse_ami_id" {
  type = string
}

variable "clickhouse_volume_size" {
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
