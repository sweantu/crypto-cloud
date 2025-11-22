output "flink_scripts_bucket_name" {
  value = aws_s3_bucket.flink_scripts.bucket
}

output "flink_scripts_bucket_arn" {
  value = aws_s3_bucket.flink_scripts.arn
}
