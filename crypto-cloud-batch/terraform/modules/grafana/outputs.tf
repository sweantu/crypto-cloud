output "grafana_cluster_name" {
  value = aws_ecs_cluster.grafana_cluster.name
}

output "grafana_security_group" {
  value = aws_security_group.grafana_sg.id
}

output "ecs_task_execution_role_name" {
  value = aws_iam_role.ecs_task_execution_role.name
}

output "grafana_service_name" {
  value = aws_ecs_service.grafana_service.name
}
