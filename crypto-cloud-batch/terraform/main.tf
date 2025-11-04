terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  required_version = ">= 1.5.0"
}

provider "aws" {
  region  = var.region
  profile = var.profile
}

# Create S3 bucket for local Spark test
resource "aws_s3_bucket" "pyspark_local" {
  bucket = var.bucket_name

  tags = {
    Project     = "pyspark-local-test"
    Environment = "dev"
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "pyspark_local" {
  bucket = aws_s3_bucket.pyspark_local.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# (Optional) Enable bucket ownership for Spark/Hadoop compatibility
resource "aws_s3_bucket_ownership_controls" "pyspark_local" {
  bucket = aws_s3_bucket.pyspark_local.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# -----------------------------
# DynamoDB table for Iceberg locking
# -----------------------------
resource "aws_dynamodb_table" "iceberg_lock_table" {
  name         = "iceberg-lock-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lock_key"

  attribute {
    name = "lock_key"
    type = "S"
  }

  tags = {
    Project     = "pyspark-local-test"
    Environment = "dev"
  }
}
