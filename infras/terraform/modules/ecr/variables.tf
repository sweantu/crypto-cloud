variable "project_prefix" { type = string }

variable "ecr_maps" {
  type = map(object({
    name = string
  }))
}
