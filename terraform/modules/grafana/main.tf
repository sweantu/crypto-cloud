resource "aws_cloudwatch_log_group" "grafana_logs" {
  name              = "/ecs/grafana"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "grafana_task" {
  family                   = "${var.project_prefix}-grafana-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = aws_iam_role.grafana_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "grafana"
      image     = "grafana/grafana:11.2.0"
      essential = true
      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "GF_SECURITY_ADMIN_USER", value = var.grafana_admin_username },
        { name = "GF_SECURITY_ADMIN_PASSWORD", value = var.grafana_admin_password },
        { name = "GF_INSTALL_PLUGINS", value = "volkovlabs-echarts-panel" },
      ]
      mountPoints = [
        {
          sourceVolume  = "grafana-storage"
          containerPath = "/var/lib/grafana"
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.grafana_logs.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  volume {
    name = "grafana-storage"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.grafana_fs.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.grafana_ap.id
      }
    }
  }

}

resource "aws_ecs_service" "grafana_service" {
  name                   = "grafana-service"
  cluster                = var.ecs_cluster_id
  task_definition        = aws_ecs_task_definition.grafana_task.arn
  desired_count          = 0
  launch_type            = "FARGATE"
  enable_execute_command = true
  platform_version       = "LATEST"

  network_configuration {
    subnets          = [var.public_subnet_ids[0]]
    security_groups  = [aws_security_group.grafana_sg.id]
    assign_public_ip = true
  }

  depends_on = [
    aws_efs_access_point.grafana_ap, aws_cloudwatch_log_group.grafana_logs
  ]
}
