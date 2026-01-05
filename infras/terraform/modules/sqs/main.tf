resource "aws_sqs_queue" "crypto_events_dlq" {
  name = "${var.project_prefix}-crypto-events-dlq"
}

resource "aws_sqs_queue" "crypto_events" {
  name                       = "${var.project_prefix}-crypto-events-queue"
  visibility_timeout_seconds = 300   # must be > max worker processing time
  message_retention_seconds  = 86400 # 1 day
  delay_seconds              = 0
  max_message_size           = 262144 # 256 KB

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.crypto_events_dlq.arn
    maxReceiveCount     = 5
  })
}

# resource "aws_cloudwatch_metric_alarm" "sqs_queue_depth" {
#   alarm_name          = "crypto-sqs-depth"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = 2
#   metric_name         = "ApproximateNumberOfMessagesVisible"
#   namespace           = "AWS/SQS"
#   period              = 60
#   statistic           = "Average"
#   threshold           = 50

#   dimensions = {
#     QueueName = aws_sqs_queue.crypto_events.name
#   }
# }
