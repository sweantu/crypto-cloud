output "flink_scripts_bucket_name" {
  value = aws_s3_bucket.flink_scripts.bucket
}

output "kinesis_example_job_name" {
  value = aws_kinesisanalyticsv2_application.kinesis_example_job.name
}
