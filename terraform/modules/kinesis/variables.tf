variable "shard_count" {
  type    = number
  default = 1
}
variable "retention_hours" {
  type    = number
  default = 24
}

variable "project_prefix" {
  type = string
}
