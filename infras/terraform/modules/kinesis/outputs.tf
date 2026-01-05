output "stream_names" {
  value = { for k, v in aws_kinesis_stream.crypto_stream_example : k => v.name }
}

output "stream_arns" {
  value = { for k, v in aws_kinesis_stream.crypto_stream_example : k => v.arn }
}
