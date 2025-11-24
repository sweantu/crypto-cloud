resource "aws_ecs_cluster" "this" {
  name = "${var.project_prefix}-cluster"
}

resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_prefix}-ecsExecutionRole"

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


resource "aws_iam_role_policy_attachment" "ecs_execution_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy",
  ])
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = each.key
}

