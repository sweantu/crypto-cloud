output "s3_bucket_name" {
  value = aws_s3_bucket.pyspark_local.bucket
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.pyspark_local.arn
}

output "dynamodb_lock_table" {
  value = aws_dynamodb_table.iceberg_lock_table.name
}