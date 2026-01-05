output "airflow_repo_url" {
  value = aws_ecr_repository.airflow_repo.repository_url
}

output "aggtrades_producer_repo_url" {
  value = aws_ecr_repository.aggtrades_producer_repo.repository_url
}

output "aggtrades_consumer_repo_url" {
  value = aws_ecr_repository.aggtrades_consumer_repo.repository_url
}
