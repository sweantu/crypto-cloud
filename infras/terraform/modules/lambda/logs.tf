resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${aws_lambda_function.aggtrades_producer_lambda.function_name}"
  retention_in_days = 7

  lifecycle {
    prevent_destroy = false
  }
}
