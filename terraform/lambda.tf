# Package lambda code into a ZIP
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/scanner"
  output_path = "${path.module}/../lambda/scanner.zip"
}

resource "aws_lambda_function" "scanner" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  function_name    = "${var.project_name}-scanner"
  role             = aws_iam_role.lambda_role.arn
  handler          = "main.lambda_handler"
  runtime          = "python3.11"
  timeout          = 300  # 5 minutes
  memory_size      = 256

  environment {
    variables = {
      SNS_TOPIC_ARN    = aws_sns_topic.alerts.arn
      DYNAMODB_TABLE   = aws_dynamodb_table.findings.name
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }
}

# Allow EventBridge to invoke Lambda
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scanner.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_scan.arn
}
