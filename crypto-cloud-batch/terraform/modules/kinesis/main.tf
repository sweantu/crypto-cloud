variable "project_prefix" { type = string }
variable "environment" { type = string }
variable "project" { type = string }
variable "shard_count" {
  type    = number
  default = 1
}
variable "retention_hours" {
  type    = number
  default = 24
}

resource "aws_kinesis_stream" "crypto_stream" {
  name = "${var.project_prefix}-kinesis-stream"
  #   shard_count      = var.shard_count
  retention_period = var.retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
    "IteratorAgeMilliseconds",
  ]

  stream_mode_details {
    stream_mode = "ON_DEMAND" # pay per request (simpler & cheaper for small scale)
  }

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

output "stream_name" {
  value = aws_kinesis_stream.crypto_stream.name
}

output "stream_arn" {
  value = aws_kinesis_stream.crypto_stream.arn
}
