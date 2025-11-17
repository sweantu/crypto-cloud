resource "aws_s3_bucket" "data_lake_bucket" {
  bucket        = "${var.project_prefix}-${var.bucket_name}"
  force_destroy = true

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "data_lake_bucket" {
  bucket = aws_s3_bucket.data_lake_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable bucket ownership for Spark/Hadoop compatibility
resource "aws_s3_bucket_ownership_controls" "data_lake_bucket" {
  bucket = aws_s3_bucket.data_lake_bucket.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# -----------------------------
# DynamoDB table for Iceberg locking
# -----------------------------
resource "aws_dynamodb_table" "iceberg_lock_table" {
  name         = "${replace(var.project_prefix, "-", "_")}_${var.iceberg_lock_table_name}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lock_key"

  attribute {
    name = "lock_key"
    type = "S"
  }

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}
