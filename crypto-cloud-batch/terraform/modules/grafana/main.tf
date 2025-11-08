# -------------------
# Security Group
# -------------------
resource "aws_security_group" "grafana_sg" {
  name        = "${var.project_prefix}-grafana-sg"
  description = "Allow Grafana HTTP access"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # For demo; restrict later
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_prefix}-grafana-sg"
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_security_group" "efs_sg" {
  name   = "${var.project_prefix}-efs-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.grafana_sg.id] # allow ECS tasks
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# -------------------
# EFS (1 mount target)
# -------------------
resource "aws_efs_file_system" "grafana_fs" {
  creation_token = "grafana-efs"
  tags = {
    Name        = "${var.project_prefix}-grafana-efs"
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_efs_mount_target" "grafana_mt" {
  file_system_id  = aws_efs_file_system.grafana_fs.id
  subnet_id       = var.public_subnet_ids[0]
  security_groups = [aws_security_group.efs_sg.id]
}

# -------------------
# EFS Access Point for Grafana
# -------------------
resource "aws_efs_access_point" "grafana_ap" {
  file_system_id = aws_efs_file_system.grafana_fs.id

  posix_user {
    uid = 472
    gid = 472
  }

  root_directory {
    path = "/grafana"
    creation_info {
      owner_uid   = 472
      owner_gid   = 472
      permissions = "755"
    }
  }

  tags = {
    Name        = "${var.project_prefix}-grafana-ap"
    Environment = var.environment
    Project     = var.project
  }
}


# -------------------
# ECS Cluster
# -------------------
resource "aws_ecs_cluster" "grafana_cluster" {
  name = "${var.project_prefix}-grafana-cluster"
}

# -------------------
# IAM Role for ECS Task
# -------------------
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${var.project_prefix}-ecsTaskExecutionRole-grafana-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
      Action = "sts:AssumeRole"
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

resource "aws_cloudwatch_log_group" "grafana_logs" {
  name              = "/ecs/grafana"
  retention_in_days = 7
}

# -------------------
# Task Definition
# -------------------
resource "aws_ecs_task_definition" "grafana_task" {
  family                   = "grafana-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn

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
        { name = "GF_SECURITY_ADMIN_USER", value = "admin" },
        { name = "GF_SECURITY_ADMIN_PASSWORD", value = "admin" },
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
          awslogs-region        = "ap-southeast-1"
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

# -------------------
# ECS Service
# -------------------
resource "aws_ecs_service" "grafana_service" {
  name                   = "grafana-service"
  cluster                = aws_ecs_cluster.grafana_cluster.id
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
