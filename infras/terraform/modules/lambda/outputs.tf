output "aggtrades_producer_lambda_name" {
  value = aws_lambda_function.aggtrades_producer_lambda.function_name
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}
