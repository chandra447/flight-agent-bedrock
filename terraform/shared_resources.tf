# Shared resources for travel booking multi-agent system

# S3 access policy for Lambda functions to access the travel database
resource "aws_iam_policy" "lambda_s3_access" {
  name        = "travel-agents-s3-access"
  description = "IAM policy for Lambda functions to access travel booking database in S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}/${var.s3_db_key}",
          "arn:aws:s3:::${var.s3_bucket_name}/backups/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${var.s3_bucket_name}"
        Condition = {
          StringLike = {
            "s3:prefix" = [
              var.s3_db_key,
              "backups/*"
            ]
          }
        }
      }
    ]
  })

  tags = var.common_tags
}

# Create Lambda packages directory
resource "null_resource" "create_lambda_packages_dir" {
  provisioner "local-exec" {
    command = "mkdir -p ${path.module}/../lambda_packages"
  }
}

# Data sources are defined in main.tf to avoid duplication
