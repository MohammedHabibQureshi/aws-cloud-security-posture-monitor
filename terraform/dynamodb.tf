resource "aws_dynamodb_table" "findings" {
  name           = "${var.project_name}-findings"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "finding_id"
  range_key      = "timestamp"

  attribute {
    name = "finding_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }
}