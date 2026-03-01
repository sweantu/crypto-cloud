resource "aws_ecr_repository" "repos" {
  for_each             = var.ecr_maps
  name                 = each.value.name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "repo_policies" {
  for_each   = var.ecr_maps
  repository = aws_ecr_repository.repos[each.key].name
  policy     = local.ecr_lifecycle_policy
}
