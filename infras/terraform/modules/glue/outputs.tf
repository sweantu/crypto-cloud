output "glue_jobs_names" {
  value = [for job in aws_glue_job.jobs : job.name]
}
