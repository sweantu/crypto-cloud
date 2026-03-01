variable "project_prefix" {
  type = string
}

variable "glue_scripts_directory" {
  type = string
}

variable "glue_jobs_map" {
  type = map(object({
    name            = string
    extra_arguments = map(string)
  }))
}
