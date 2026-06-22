terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # Uncomment to use S3 backend for team use
  # backend "s3" {
  #   bucket = "your-tfstate-bucket"
  #   key    = "cspm/terraform.tfstate"
  #   region = "ap-south-1"
  # }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project     = "aws-cspm"
      ManagedBy   = "Terraform"
      Environment = "dev"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
