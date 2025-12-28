output "crypto_sqs_queue_url" {
  value = aws_sqs_queue.crypto_events.url
}

output "crypto_sqs_queue_arn" {
  value = aws_sqs_queue.crypto_events.arn
}

output "crypto_sqs_queue_name" {
  value = aws_sqs_queue.crypto_events.name
}

output "crypto_sqs_dlq_url" {
  value = aws_sqs_queue.crypto_events_dlq.url
}

output "crypto_sqs_dlq_arn" {
  value = aws_sqs_queue.crypto_events_dlq.arn
}
