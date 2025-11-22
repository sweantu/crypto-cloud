variable "project_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "stream_arns" {
  type = map(string)
}

variable "scripts_bucket_arn" {
  type = string
}

variable "data_lake_bucket" {
  type = string
}
