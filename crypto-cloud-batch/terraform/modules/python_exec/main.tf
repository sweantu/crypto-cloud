variable "project_prefix" {}
variable "vpc_id" {}
variable "public_subnet_ids" { type = list(string) }
variable "environment" {}
variable "project" {}

# --- Security group ---
resource "aws_security_group" "python_exec_sg" {
  name   = "${var.project_prefix}-python-exec-sg"
  vpc_id = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- CloudWatch logs ---
resource "aws_cloudwatch_log_group" "python_exec_logs" {
  name              = "/ecs/python-test"
  retention_in_days = 7
}

# --- ECS cluster ---
resource "aws_ecs_cluster" "python_exec_cluster" {
  name = "${var.project_prefix}-python-exec-cluster"
}

# --- IAM role for ECS Task Execution ---
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_prefix}-ecsTaskExecutionRole-python"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  ])
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = each.key
}

# --- Task Definition ---
resource "aws_ecs_task_definition" "python_exec_task" {
  family                   = "python-exec-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "python"
      image     = "public.ecr.aws/amazonlinux/amazonlinux:2023"
      essential = true
      command   = ["bash", "-c", "dnf install -y python3.11 && echo hello-sweantu!!! && sleep 3600"]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.python_exec_logs.name
          awslogs-region        = "ap-southeast-1"
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

# --- ECS Service ---
resource "aws_ecs_service" "python_exec_service" {
  name                   = "python-exec-service"
  cluster                = aws_ecs_cluster.python_exec_cluster.id
  task_definition        = aws_ecs_task_definition.python_exec_task.arn
  desired_count          = 0
  launch_type            = "FARGATE"
  enable_execute_command = true
  platform_version       = "LATEST"

  network_configuration {
    subnets          = [var.public_subnet_ids[0]]
    security_groups  = [aws_security_group.python_exec_sg.id]
    assign_public_ip = true
  }

  depends_on = [aws_cloudwatch_log_group.python_exec_logs]
}

# --- Outputs ---
output "python_exec_cluster" {
  value = aws_ecs_cluster.python_exec_cluster.name
}

output "python_exec_service" {
  value = aws_ecs_service.python_exec_service.name
}
