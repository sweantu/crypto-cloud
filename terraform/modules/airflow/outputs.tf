output "airflow_db_endpoint" {
  value = aws_db_instance.airflow_db.address
}

output "airflow_ecs_service_name" {
  value = aws_ecs_service.airflow_service.name
}

output "airflow_db_identifier" {
  value = aws_db_instance.airflow_db.identifier
}
