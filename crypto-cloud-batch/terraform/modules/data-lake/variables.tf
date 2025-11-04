variable "project" {
  description = "Project name for tagging resources"
  type        = string
}

variable "environment" {
  description = "Environment name for tagging resources"
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket for PySpark testing"
  type        = string
}

variable "iceberg_lock_table_name" {
  description = "DynamoDB table for Iceberg locking"
  type        = string
}

variable "project_prefix" {
  description = "Project prefix for naming resources"
  type        = string
}
