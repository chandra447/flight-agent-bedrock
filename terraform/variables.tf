# Variables for travel booking multi-agent system

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Environment name (production, test, etc.)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "bedrock-multi-agent"
}

variable "foundation_model" {
  description = "Foundation model to use for all agents"
  type        = string
  default     = "mistral.mistral-7b-instruct-v0:2"
}

variable "s3_bucket_name" {
  description = "S3 bucket name containing the travel booking database"
  type        = string
  default     = "travel-agent-data"
}

variable "s3_db_key" {
  description = "S3 key for the travel booking database file"
  type        = string
  default     = "travel_booking.db"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "TravelBookingMultiAgent"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 14
}