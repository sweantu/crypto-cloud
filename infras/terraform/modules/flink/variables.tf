variable "project_prefix" {
  type = string
}

variable "region" {
  type = string
}

variable "scripts_bucket_arn" {
  type = string
}

variable "stream_info_map" {
  type = map(object({
    name = string
    arn  = string
  }))
}

variable "clickhouse_info" {
  type = object({
    url      = string
    database = string
    username = string
    password = string
  })
}
