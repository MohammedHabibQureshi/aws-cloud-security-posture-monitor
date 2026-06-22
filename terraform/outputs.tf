output "lambda_arn" {
  value = aws_lambda_function.scanner.arn
}
output "dashboard_url" {
  value = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home#dashboards:name=${aws_cloudwatch_dashboard.cspm.dashboard_name}"
}
output "dynamodb_table" {
  value = aws_dynamodb_table.findings.name
}
