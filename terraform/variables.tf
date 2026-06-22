variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "cspm"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  sensitive   = true
}

variable "alert_email" {
  description = "Email address for SNS alerts"
  type        = string
}

variable "scan_schedule" {
  description = "EventBridge cron for daily scan"
  type        = string
  default     = "cron(0 6 * * ? *)"
}