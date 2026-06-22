resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Managed policies
resource "aws_iam_role_policy_attachment" "basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for CSPM read access
resource "aws_iam_role_policy" "cspm_policy" {
  name = "${var.project_name}-policy"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = [
          "iam:GetAccountSummary", "iam:GetAccountPasswordPolicy",
          "iam:ListUsers", "iam:ListAccessKeys", "iam:ListUserPolicies",
          "iam:GenerateCredentialReport", "iam:GetCredentialReport"],
        Resource = "*" },
      { Effect = "Allow", Action = [
          "s3:ListAllMyBuckets", "s3:GetBucketPublicAccessBlock",
          "s3:GetBucketEncryption", "s3:GetBucketVersioning", "s3:GetBucketLogging"],
        Resource = "*" },
      { Effect = "Allow", Action = [
          "ec2:DescribeSecurityGroups", "ec2:DescribeInstances",
          "ec2:GetEbsEncryptionByDefault"],
        Resource = "*" },
      { Effect = "Allow", Action = ["cloudtrail:DescribeTrails", "cloudtrail:GetTrailStatus"],
        Resource = "*" },
      { Effect = "Allow", Action = ["dynamodb:PutItem", "dynamodb:BatchWriteItem"],
        Resource = aws_dynamodb_table.findings.arn },
      { Effect = "Allow", Action = ["sns:Publish"],
        Resource = aws_sns_topic.alerts.arn },
      { Effect = "Allow", Action = ["cloudwatch:PutMetricData"],
        Resource = "*" }
    ]
  })
}
