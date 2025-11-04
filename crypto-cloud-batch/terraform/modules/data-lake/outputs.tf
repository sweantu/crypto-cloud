output "data_lake_bucket_name" {
  value = aws_s3_bucket.data_lake_bucket.bucket
}

output "data_lake_bucket_arn" {
  value = aws_s3_bucket.data_lake_bucket.arn
}

output "data_lake_iceberg_lock_table_name" {
  value = aws_dynamodb_table.iceberg_lock_table.name
}
