output "grafana_cluster_name" {
  value = aws_ecs_cluster.grafana_cluster.name
}

output "grafana_efs_id" {
  value = aws_efs_file_system.grafana_fs.id
}

output "grafana_security_group" {
  value = aws_security_group.grafana_sg.id
}

