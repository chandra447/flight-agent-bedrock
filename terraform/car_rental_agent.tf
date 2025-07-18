# Car Rental Agent Terraform Configuration
# Creates the car rental specialist agent with Lambda action groups

# Lambda function for car rental operations
resource "aws_lambda_function" "car_rental_lambda" {
  filename         = data.archive_file.car_rental_lambda_zip.output_path
  function_name    = "car-rental-agent-lambda"
  role            = aws_iam_role.car_rental_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  source_code_hash = data.archive_file.car_rental_lambda_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket_name
      S3_DB_KEY = var.s3_db_key
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.car_rental_lambda_basic,
    aws_iam_role_policy_attachment.car_rental_lambda_s3,
    aws_cloudwatch_log_group.car_rental_lambda_logs,
  ]

  tags = var.common_tags
}

# Create Lambda deployment package
data "archive_file" "car_rental_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/../lambda_packages/car_rental_lambda.zip"
  
  source {
    content = templatefile("${path.module}/../lambda_functions/car_rental_agent/lambda_function.py", {
      # Template variables if needed
    })
    filename = "lambda_function.py"
  }
  
  source {
    content  = file("${path.module}/../database/db_utils.py")
    filename = "db_utils.py"
  }

  depends_on = [null_resource.create_lambda_packages_dir]
}

# IAM role for Lambda function
resource "aws_iam_role" "car_rental_lambda_role" {
  name = "car-rental-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "car_rental_lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.car_rental_lambda_role.name
}

# S3 access policy for database
resource "aws_iam_role_policy_attachment" "car_rental_lambda_s3" {
  policy_arn = aws_iam_policy.lambda_s3_access.arn
  role       = aws_iam_role.car_rental_lambda_role.name
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "car_rental_lambda_logs" {
  name              = "/aws/lambda/car-rental-agent-lambda"
  retention_in_days = var.log_retention_days
  tags              = var.common_tags
}

# Lambda permission for Bedrock agent
resource "aws_lambda_permission" "car_rental_bedrock_invoke" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.car_rental_lambda.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = module.car_rental_agent.agent_arn
}

# Car Rental Agent using auto-agents module
module "car_rental_agent" {
  source = "../modules/auto-agents"

  # Basic agent configuration
  agent_name        = "car-rental-agent"
  agent_description = "Car Rental Agent specialized in vehicle rental services, fleet management, and ground transportation solutions"
  foundation_model  = var.foundation_model
  agent_instruction = file("${path.module}/../agent_instructions/car_rental_instruction.txt")

  # Collaborator configuration (not supervisor)
  agent_collaboration = null
  prepare_agent      = true

  # Memory configuration
  memory_configuration = {
    enabled      = true
    storage_days = 7
  }

  # Action groups for car rental operations
  action_groups = [
    {
      name        = "car-rental-operations"
      description = "Vehicle search, rental booking, and rental management operations"
      action_group_executor = {
        lambda = aws_lambda_function.car_rental_lambda.arn
      }
      function_schema = {
        member_functions = {
          functions = [
            {
              name        = "search_cars"
              description = "Search for available rental vehicles based on location and dates"
              parameters = [
                {
                  map_block_key = "pickup_location"
                  type          = "string"
                  description   = "Pickup location (city, airport, or address)"
                  required      = true
                },
                {
                  map_block_key = "dropoff_location"
                  type          = "string"
                  description   = "Drop-off location (city, airport, or address)"
                  required      = true
                },
                {
                  map_block_key = "pickup_date"
                  type          = "string"
                  description   = "Pickup date and time in YYYY-MM-DD HH:MM:SS format"
                  required      = true
                },
                {
                  map_block_key = "dropoff_date"
                  type          = "string"
                  description   = "Drop-off date and time in YYYY-MM-DD HH:MM:SS format"
                  required      = true
                },
                {
                  map_block_key = "car_type"
                  type          = "string"
                  description   = "Preferred vehicle category (Economy, Compact, Mid-size, Full-size, SUV, Luxury)"
                  required      = false
                }
              ]
            },
            {
              name        = "book_car"
              description = "Book a selected rental vehicle with driver details"
              parameters = [
                {
                  map_block_key = "car_id"
                  type          = "string"
                  description   = "ID of the vehicle to book"
                  required      = true
                },
                {
                  map_block_key = "pickup_location_id"
                  type          = "string"
                  description   = "ID of the pickup location"
                  required      = true
                },
                {
                  map_block_key = "dropoff_location_id"
                  type          = "string"
                  description   = "ID of the drop-off location"
                  required      = true
                },
                {
                  map_block_key = "pickup_date"
                  type          = "string"
                  description   = "Pickup date and time in YYYY-MM-DD HH:MM:SS format"
                  required      = true
                },
                {
                  map_block_key = "dropoff_date"
                  type          = "string"
                  description   = "Drop-off date and time in YYYY-MM-DD HH:MM:SS format"
                  required      = true
                },
                {
                  map_block_key = "driver_details"
                  type          = "string"
                  description   = "JSON string containing driver information and insurance options"
                  required      = true
                }
              ]
            },
            {
              name        = "cancel_rental"
              description = "Cancel a car rental booking and process refund"
              parameters = [
                {
                  map_block_key = "booking_id"
                  type          = "string"
                  description   = "Car rental booking ID or reference to cancel"
                  required      = true
                }
              ]
            }
          ]
        }
      }
    }
  ]

  # Agent aliases
  agent_aliases = [
    {
      name        = "PROD"
      description = "Production alias for car rental agent"
      tags        = var.common_tags
    }
  ]

  # No collaborators for specialist agents
  collaborators = []

  # Tags
  agent_tags = merge(var.common_tags, {
    Agent = "CarRental"
    Role  = "Specialist"
  })
}

# Outputs
output "car_rental_agent_id" {
  description = "ID of the car rental agent"
  value       = module.car_rental_agent.agent_id
}

output "car_rental_agent_arn" {
  description = "ARN of the car rental agent"
  value       = module.car_rental_agent.agent_arn
}

output "car_rental_alias_arn" {
  description = "ARN of the car rental agent PROD alias"
  value       = module.car_rental_agent.agent_alias_arns["PROD"]
}

output "car_rental_lambda_arn" {
  description = "ARN of the car rental Lambda function"
  value       = aws_lambda_function.car_rental_lambda.arn
}