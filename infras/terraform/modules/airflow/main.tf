resource "aws_security_group" "airflow_sg" {
  name   = "${var.project_prefix}-airflow-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "airflow_logs" {
  name              = "/ecs/airflow"
  retention_in_days = 7
}

resource "aws_iam_role" "airflow_task_role" {
  name = "${var.project_prefix}-airflow-task-role"

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

resource "aws_iam_role_policy" "airflow_policy" {
  name = "${var.project_prefix}-airflow-policy"
  role = aws_iam_role.airflow_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:*", "glue:*", "s3:*"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_ecs_task_definition" "airflow_task" {
  family                   = "${var.project_prefix}-airflow-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = var.ecs_execution_role_arn
  task_role_arn            = aws_iam_role.airflow_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "airflow"
      image     = "${var.airflow_repo_url}:latest"
      essential = true
      portMappings = [
        { containerPort = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "AIRFLOW__CORE__EXECUTOR", value = "LocalExecutor" },
        { name = "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", value = "postgresql+psycopg2://${var.airflow_db_username}:${var.airflow_db_password}@${aws_db_instance.airflow_db.address}:5432/${var.airflow_db_name}" },
        { name = "AIRFLOW__CORE__FERNET_KEY", value = var.airflow_fernet_key },
        { name = "AIRFLOW__CORE__LOAD_EXAMPLES", value = "False" },
        { name = "AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL", value = "10" },
        { name = "AIRFLOW__CORE__DEFAULT_TIMEZONE", value = "UTC" },
        { name = "AIRFLOW_ADMIN_USERNAME", value = var.airflow_admin_username },
        { name = "AIRFLOW_ADMIN_PASSWORD", value = var.airflow_admin_password },
        { name = "AIRFLOW_ADMIN_EMAIL", value = var.airflow_admin_email },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.airflow_logs.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "airflow_service" {
  name                   = "airflow-service"
  cluster                = var.ecs_cluster_id
  task_definition        = aws_ecs_task_definition.airflow_task.arn
  desired_count          = 0
  launch_type            = "FARGATE"
  enable_execute_command = true
  platform_version       = "LATEST"

  network_configuration {
    subnets          = [var.public_subnet_ids[0]]
    security_groups  = [aws_security_group.airflow_sg.id]
    assign_public_ip = true
  }

  depends_on = [
    aws_cloudwatch_log_group.airflow_logs
  ]
}

