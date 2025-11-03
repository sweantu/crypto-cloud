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

variable "bucket_name" {
  description = "Name of the S3 bucket for PySpark testing"
  type        = string
  default     = "pyspark-local-test-bucket"
}
