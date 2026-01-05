resource "aws_cloudwatch_log_group" "flink_logs" {
  name              = "/aws/flink-applications"
  retention_in_days = 7
}


