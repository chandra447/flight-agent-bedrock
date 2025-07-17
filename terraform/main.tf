# Main Terraform configuration for Travel Booking Multi-Agent System
# This file orchestrates the deployment of all travel booking agents

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = var.common_tags
  }
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Local values
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
}