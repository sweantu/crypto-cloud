resource "aws_kinesis_stream" "crypto_stream_example" {
  for_each = toset([
    # "ExampleInputStream",
    # "ExampleOutputStream",
    "${var.project_prefix}-aggtrades-stream",
  ])
  name             = each.key
  shard_count      = var.shard_count
  retention_period = var.retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
    "IteratorAgeMilliseconds",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}
