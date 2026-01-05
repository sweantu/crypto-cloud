resource "aws_security_group" "aggtrades_producer_sg" {
  name   = "${var.project_prefix}-aggtrades-producer-sg"
  vpc_id = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "aggtrades_producer_logs" {
  name              = "/ecs/aggtrades-producer"
  retention_in_days = 7
}

resource "aws_iam_role" "aggtrades_producer_task_role" {
  name = "${var.project_prefix}-aggtrades-producer-task-role"

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

resource "aws_iam_role_policy" "aggtrades_producer_policy" {
  name = "${var.project_prefix}-aggtrades-producer-policy"
  role = aws_iam_role.aggtrades_producer_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:*", "kinesis:*"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_ecs_task_definition" "aggtrades_producer_task" {
  family                   = "${var.project_prefix}-aggtrades-producer-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = aws_iam_role.aggtrades_producer_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "aggtrades-producer"
      image     = "${var.aggtrades_producer_repo_url}:latest"
      essential = true

      command = [
        "--symbols", var.default_symbols,
        "--landing_dates", var.default_landing_dates
      ]

      environment = [
        {
          name  = "AGGTRADES_STREAM_NAME"
          value = var.aggtrades_stream_name
        },
        {
          name  = "REGION"
          value = var.region
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.aggtrades_producer_logs.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "aggtrades_producer_service" {
  name                   = "aggtrades-producer-service"
  cluster                = var.ecs_cluster_id
  task_definition        = aws_ecs_task_definition.aggtrades_producer_task.arn
  desired_count          = 0
  launch_type            = "FARGATE"
  enable_execute_command = true
  platform_version       = "LATEST"

  network_configuration {
    subnets          = [var.public_subnet_ids[0]]
    security_groups  = [aws_security_group.aggtrades_producer_sg.id]
    assign_public_ip = true
  }

  depends_on = [
    aws_cloudwatch_log_group.aggtrades_producer_logs
  ]
}

