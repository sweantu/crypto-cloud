variable "region" {
  description = "AWS region to create the bucket"
  type        = string
  default     = "ap-southeast-1"
}

variable "profile" {
  description = "AWS CLI profile to use"
  type        = string
  default     = "default"
}

variable "project" {
  description = "Project name for tagging resources"
  type        = string
  default     = "crypto-cloud"
}

variable "environment" {
  description = "Environment name for tagging resources"
  type        = string
  default     = "dev"
}

variable "data_lake_bucket_name" {
  description = "Name of the S3 bucket for PySpark testing"
  type        = string
  default     = "data-lake-bucket"
}

variable "data_lake_iceberg_lock_table_name" {
  description = "DynamoDB table for Iceberg locking"
  type        = string
  default     = "iceberg_lock_table"
}

variable "glue_scripts_bucket_name" {
  description = "Name of the S3 bucket for Glue scripts"
  type        = string
  default     = "glue-scripts-bucket"
}