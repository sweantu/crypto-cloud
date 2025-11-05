output "glue_scripts_bucket_name" {
  value = aws_s3_bucket.glue_scripts.bucket
}

output "glue_scripts_bucket_arn" {
  value = aws_s3_bucket.glue_scripts.arn
}

output "landing_job_name" {
  value = aws_glue_job.landing_job.name
}
