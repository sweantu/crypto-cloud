output "glue_scripts_bucket_name" {
  value = aws_s3_bucket.glue_scripts.bucket
}

output "landing_job_name" {
  value = aws_glue_job.landing_job.name
}

output "transform_job_name" {
  value = aws_glue_job.transform_job.name
}

output "transform_job_pattern_two_name" {
  value = aws_glue_job.transform_job_pattern_two.name
}
