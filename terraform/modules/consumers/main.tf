resource "aws_security_group" "aggtrades_consumer_sg" {
  name   = "${var.project_prefix}-aggtrades-consumer-sg"
  vpc_id = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "aggtrades_consumer_logs" {
  name              = "/ecs/aggtrades-consumer"
  retention_in_days = 7
}

resource "aws_iam_role" "aggtrades_consumer_task_role" {
  name = "${var.project_prefix}-aggtrades-consumer-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "aggtrades_consumer_policy" {
  name = "${var.project_prefix}-aggtrades-consumer-policy"
  role = aws_iam_role.aggtrades_consumer_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:*", "kinesis:*", "sqs:*"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_ecs_task_definition" "aggtrades_consumer_task" {
  family                   = "${var.project_prefix}-aggtrades-consumer-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = aws_iam_role.aggtrades_consumer_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "aggtrades-consumer"
      image     = "${var.aggtrades_consumer_repo_url}:latest"
      essential = true

      command = [
        "--name", var.crypto_sqs_queue_url
      ]

      environment = [
        {
          name  = "REGION"
          value = var.region
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.aggtrades_consumer_logs.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "aggtrades_consumer_service" {
  name                   = "aggtrades-consumer-service"
  cluster                = var.ecs_cluster_id
  task_definition        = aws_ecs_task_definition.aggtrades_consumer_task.arn
  desired_count          = 0
  launch_type            = "FARGATE"
  enable_execute_command = true
  platform_version       = "LATEST"

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = [var.public_subnet_ids[0]]
    security_groups  = [aws_security_group.aggtrades_consumer_sg.id]
    assign_public_ip = true
  }

  depends_on = [
    aws_cloudwatch_log_group.aggtrades_consumer_logs
  ]
}

