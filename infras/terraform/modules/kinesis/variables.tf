variable "streams_props_map" {
  description = "A map of Kinesis stream names to their properties (shard count and retention hours)"
  type = map(object({
    name            = string
    shard_count     = number
    retention_hours = number
  }))
}
