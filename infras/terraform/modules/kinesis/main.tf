resource "aws_kinesis_stream" "crypto_stream" {
  for_each         = var.streams_props_map
  name             = each.value.name
  shard_count      = each.value.shard_count
  retention_period = each.value.retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "OutgoingBytes",
    "IteratorAgeMilliseconds",
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }
}
