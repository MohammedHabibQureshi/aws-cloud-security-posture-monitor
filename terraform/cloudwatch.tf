resource "aws_cloudwatch_dashboard" "cspm" {
  dashboard_name = "${var.project_name}-dashboard"
  dashboard_body = jsonencode({
    widgets = [
      { 
        type = "metric", x = 0, y = 0, width = 12, height = 6, 
        properties = {
          region = var.aws_region
          title  = "Findings by Severity"
          metrics = [
            ["CSPM/SecurityFindings", "FindingsBySeverity", "Severity", "CRITICAL"],
            ["CSPM/SecurityFindings", "FindingsBySeverity", "Severity", "HIGH"]
          ]
          period = 86400
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
      { 
        type = "metric", x = 12, y = 0, width = 12, height = 6, 
        properties = {
          region = var.aws_region
          title  = "Total Findings Trend"
          metrics = [["CSPM/SecurityFindings", "TotalFindings"]]
          period  = 86400
          stat    = "Sum"
          view    = "timeSeries"
        }
      }
    ]
  })
}