resource "aws_s3_bucket" "data_lake_bucket" {
  bucket        = "${var.project_prefix}-data-lake-bucket"
  force_destroy = true
}

# Block public access
resource "aws_s3_bucket_public_access_block" "data_lake_bucket" {
  bucket                  = aws_s3_bucket.data_lake_bucket.id
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
  name         = "${var.project_prefix_underscore}_iceberg_lock_table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "lock_key"

  attribute {
    name = "lock_key"
    type = "S"
  }
}
