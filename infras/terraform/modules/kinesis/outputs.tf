output "stream_info_map" {
  value = { for k, v in aws_kinesis_stream.crypto_stream : k => {
    name = v.name
    arn  = v.arn
  } }
}
