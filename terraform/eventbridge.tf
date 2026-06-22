resource "aws_cloudwatch_event_rule" "daily_scan" {
  name                = "${var.project_name}-daily-scan"
  description         = "Trigger CSPM scan daily"
  schedule_expression = var.scan_schedule
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.daily_scan.name
  target_id = "CspamLambdaTarget"
  arn       = aws_lambda_function.scanner.arn
}
