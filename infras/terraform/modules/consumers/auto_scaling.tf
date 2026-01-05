resource "aws_appautoscaling_target" "ecs_sqs_target" {
  max_capacity       = 4 # hard ceiling
  min_capacity       = 0 # always keep 1 worker alive
  resource_id        = "service/${var.ecs_cluster_name}/${aws_ecs_service.aggtrades_consumer_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "sqs_target_tracking" {
  name               = "${var.project_prefix}-crypto-sqs-tracking"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_sqs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_sqs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_sqs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value       = 30
    scale_out_cooldown = 30
    scale_in_cooldown  = 120
    disable_scale_in   = false # ✅ VERY IMPORTANT

    customized_metric_specification {
      metric_name = "ApproximateNumberOfMessagesVisible"
      namespace   = "AWS/SQS"
      statistic   = "Average"

      dimensions {
        name  = "QueueName"
        value = var.crypto_sqs_queue_name
      }
    }
  }
}
