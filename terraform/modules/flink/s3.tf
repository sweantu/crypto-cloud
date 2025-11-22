resource "aws_s3_bucket" "flink_scripts" {
  bucket        = "${var.project_prefix}-flink-scripts"
  force_destroy = true
}
