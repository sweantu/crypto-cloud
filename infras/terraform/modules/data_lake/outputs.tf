output "data_lake_bucket_name" {
  value = aws_s3_bucket.data_lake_bucket.bucket
}

output "iceberg_lock_table_name" {
  value = aws_dynamodb_table.iceberg_lock_table.name
}

output "transform_db_name" {
  value = aws_glue_catalog_database.transform_db.name
}
