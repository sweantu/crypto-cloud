# -------------------------
# Outputs
# -------------------------
output "athena_workgroup_name" {
  value       = aws_athena_workgroup.crypto_dev.name
  description = "Athena WorkGroup name"
}

output "athena_result_path" {
  value       = "s3://${var.data_lake_bucket_name}/athena_results/"
  description = "S3 path for Athena query results"
}
