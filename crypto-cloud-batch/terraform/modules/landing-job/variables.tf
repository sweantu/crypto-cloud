variable "project" {
  description = "Project name for tagging resources"
  type        = string
}

variable "environment" {
  description = "Environment name for tagging resources"
  type        = string
}

variable "glue_scripts_bucket_name" {
  description = "Name of the S3 bucket for Glue scripts"
  type        = string
}

variable "project_prefix" {
  description = "Project prefix for naming resources"
  type        = string
}
