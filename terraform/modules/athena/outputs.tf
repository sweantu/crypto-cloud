output "athena_wg_name" {
  value = aws_athena_workgroup.athena_wg.name
}

output "athena_output_location" {
  value = "s3://${var.data_lake_bucket_name}/${var.athena_output_prefix}"
}
