resource "aws_ecr_repository" "aggtrades_consumer_repo" {
  name                 = "${var.project_prefix}-aggtrades-consumer-repo"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "aggtrades_consumer_policy" {
  repository = aws_ecr_repository.aggtrades_consumer_repo.name
  policy     = local.ecr_lifecycle_policy
}
