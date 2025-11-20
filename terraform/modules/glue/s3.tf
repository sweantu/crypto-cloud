resource "aws_s3_bucket" "glue_scripts" {
  bucket        = "${var.project_prefix}-glue-scripts"
  force_destroy = true
}
