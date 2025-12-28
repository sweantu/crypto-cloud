output "kinesis_example_job_name" {
  value = aws_kinesisanalyticsv2_application.kinesis_example_job.name
}

output "iceberg_sink_job_name" {
  value = aws_kinesisanalyticsv2_application.iceberg_sink_job.name
}
