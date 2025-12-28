
resource "aws_lambda_function" "aggtrades_producer_lambda" {
  function_name = "${var.project_prefix}-aggtrades-producer-lambda"

  handler = "main.lambda_handler"
  runtime = "python3.11"

  filename         = "${path.module}/../../../producers/aggtrades_lambda/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../producers/aggtrades_lambda/lambda.zip")

  role = aws_iam_role.lambda_role.arn

  timeout = 600

  environment {
    variables = {
      AGGTRADES_STREAM_NAME = var.kinesis_stream_name
      REGION                = var.region
    }
  }
}

