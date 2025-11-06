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
variable "data_lake_bucket_name" {
  description = "Name of the data lake S3 bucket"
  type        = string
}

variable "data_lake_iceberg_lock_table_name" {
  description = "Name of the Iceberg lock table in Glue Data Catalog"
  type        = string
}

variable "project_prefix" {
  description = "Project prefix for naming resources"
  type        = string
}

variable "glue_job_role_arn" {
  description = "ARN of the IAM role for Glue job"
  type        = string
}
