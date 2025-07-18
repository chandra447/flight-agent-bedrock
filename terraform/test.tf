# Simple test configuration to verify Terraform is working
# This creates basic AWS resources to test the deployment pipeline

# Test S3 bucket for storing travel data
resource "aws_s3_bucket" "travel_data_test" {
  bucket = "${var.project_name}-travel-data-${var.environment}-${random_id.bucket_suffix.hex}"
  
  tags = merge(var.common_tags, {
    Name = "Travel Data Test Bucket"
    Type = "Test"
  })
}

# Random ID for unique bucket naming
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "travel_data_versioning" {
  bucket = aws_s3_bucket.travel_data_test.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "travel_data_encryption" {
  bucket = aws_s3_bucket.travel_data_test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Test CloudWatch log group
resource "aws_cloudwatch_log_group" "travel_agents_test" {
  name              = "/aws/travel-agents/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days
  
  tags = merge(var.common_tags, {
    Name = "Travel Agents Test Logs"
    Type = "Test"
  })
}

# Upload the travel booking database to S3
resource "aws_s3_object" "travel_booking_db" {
  bucket = aws_s3_bucket.travel_data_test.bucket
  key    = var.s3_db_key
  source = "${path.module}/../database/travel_booking.db"
  etag   = filemd5("${path.module}/../database/travel_booking.db")
  
  tags = merge(var.common_tags, {
    Name = "Travel Booking Database"
    Type = "Database"
  })
  
  depends_on = [aws_s3_bucket.travel_data_test]
}

# Output the test resources
output "test_s3_bucket_name" {
  description = "Name of the test S3 bucket"
  value       = aws_s3_bucket.travel_data_test.bucket
}

output "test_s3_bucket_arn" {
  description = "ARN of the test S3 bucket"
  value       = aws_s3_bucket.travel_data_test.arn
}

output "test_s3_bucket_url" {
  description = "S3 URL of the travel booking database"
  value       = "s3://${aws_s3_bucket.travel_data_test.bucket}/${aws_s3_object.travel_booking_db.key}"
}

output "test_log_group_name" {
  description = "Name of the test CloudWatch log group"
  value       = aws_cloudwatch_log_group.travel_agents_test.name
}