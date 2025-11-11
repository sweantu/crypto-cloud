variable "project_prefix" { type = string }
variable "public_subnet_ids" { type = list(string) }
variable "vpc_id" { type = string }
variable "grafana_ecs_task_execution_role_name" { type = string }

resource "aws_db_subnet_group" "public" {
  name       = "${var.project_prefix}-public-db-subnet"
  subnet_ids = var.public_subnet_ids
}

resource "aws_security_group" "airflow_sg" {
  name        = "${var.project_prefix}-airflow-sg"
  vpc_id      = var.vpc_id
  description = "Allow Airflow + Postgres"

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
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

resource "aws_db_instance" "airflow_db" {
  identifier             = "${var.project_prefix}-airflow-db"
  engine                 = "postgres"
  engine_version         = "15"
  instance_class         = "db.t4g.micro"
  allocated_storage      = 20
  username               = "airflow"
  password               = "airflow123"
  publicly_accessible    = true
  skip_final_snapshot    = true
  multi_az               = false
  vpc_security_group_ids = [aws_security_group.airflow_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.public.name
}

data "aws_iam_role" "ecs_task_execution_role" {
  name = var.grafana_ecs_task_execution_role_name
}

resource "aws_cloudwatch_log_group" "airflow_logs" {
  name              = "/ecs/airflow"
  retention_in_days = 7
}

resource "aws_ecs_cluster" "airflow_cluster" {
  name = "${var.project_prefix}-airflow-cluster"
}

resource "aws_ecs_task_definition" "airflow_task" {
  family                   = "airflow_task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024"
  memory                   = "2048"
  execution_role_arn       = data.aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = data.aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "airflow"
      image     = "650251698703.dkr.ecr.ap-southeast-1.amazonaws.com/crypto-cloud-batch-airflow-adm64:latest"
      essential = true
      portMappings = [
        { containerPort = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "AIRFLOW__CORE__EXECUTOR", value = "LocalExecutor" },
        { name = "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN", value = "postgresql+psycopg2://airflow:airflow123@${aws_db_instance.airflow_db.address}:5432/airflow" },
        { name = "AIRFLOW__CORE__FERNET_KEY", value = "Jers0E9_wUUeAcywlKdthfytgqpiO7QsGfk0GMiYwjw=" },
        { name = "AIRFLOW__CORE__LOAD_EXAMPLES", value = "False" },
        { name = "AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL", value = "10" },
        { name = "AIRFLOW__CORE__DEFAULT_TIMEZONE", value = "UTC" },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.airflow_logs.name
          awslogs-region        = "ap-southeast-1"
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "airflow_service" {
  name                   = "airflow-service"
  cluster                = aws_ecs_cluster.airflow_cluster.id
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

output "airflow_db_endpoint" {
  value = aws_db_instance.airflow_db.address
}
