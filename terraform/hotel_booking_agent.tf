# Hotel Booking Agent Terraform Configuration
# Creates the hotel booking specialist agent with Lambda action groups

# Lambda function for hotel booking operations
resource "aws_lambda_function" "hotel_booking_lambda" {
  filename         = data.archive_file.hotel_booking_lambda_zip.output_path
  function_name    = "hotel-booking-agent-lambda"
  role            = aws_iam_role.hotel_booking_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  source_code_hash = data.archive_file.hotel_booking_lambda_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket_name
      S3_DB_KEY = var.s3_db_key
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.hotel_booking_lambda_basic,
    aws_iam_role_policy_attachment.hotel_booking_lambda_s3,
    aws_cloudwatch_log_group.hotel_booking_lambda_logs,
  ]

  tags = var.common_tags
}

# Create Lambda deployment package
data "archive_file" "hotel_booking_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/../lambda_packages/hotel_booking_lambda.zip"
  
  source {
    content = templatefile("${path.module}/../lambda_functions/hotel_booking_agent/lambda_function.py", {
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
resource "aws_iam_role" "hotel_booking_lambda_role" {
  name = "hotel-booking-lambda-role"

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
resource "aws_iam_role_policy_attachment" "hotel_booking_lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.hotel_booking_lambda_role.name
}

# S3 access policy for database
resource "aws_iam_role_policy_attachment" "hotel_booking_lambda_s3" {
  policy_arn = aws_iam_policy.lambda_s3_access.arn
  role       = aws_iam_role.hotel_booking_lambda_role.name
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "hotel_booking_lambda_logs" {
  name              = "/aws/lambda/hotel-booking-agent-lambda"
  retention_in_days = var.log_retention_days
  tags              = var.common_tags
}

# Lambda permission for Bedrock agent
resource "aws_lambda_permission" "hotel_booking_bedrock_invoke" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.hotel_booking_lambda.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = module.hotel_booking_agent.agent_arn
}

# Hotel Booking Agent using auto-agents module
module "hotel_booking_agent" {
  source = "../modules/auto-agents"

  # Basic agent configuration
  agent_name        = "hotel-booking-agent"
  agent_description = "Hotel Booking Agent specialized in accommodation searches, hotel reservations, and hospitality services"
  foundation_model  = var.foundation_model
  agent_instruction = file("${path.module}/../agent_instructions/hotel_booking_instruction.txt")

  # Collaborator configuration (not supervisor)
  agent_collaboration = null
  prepare_agent      = true

  # Memory configuration
  memory_configuration = {
    enabled      = true
    storage_days = 7
  }

  # Action groups for hotel operations
  action_groups = [
    {
      name        = "hotel-operations"
      description = "Hotel search, booking, and reservation management operations"
      action_group_executor = {
        lambda = aws_lambda_function.hotel_booking_lambda.arn
      }
      function_schema = {
        member_functions = {
          functions = [
            {
              name        = "search_hotels"
              description = "Search for available hotels based on location and dates"
              parameters = [
                {
                  map_block_key = "location"
                  type          = "string"
                  description   = "City or location name for hotel search"
                  required      = true
                },
                {
                  map_block_key = "check_in_date"
                  type          = "string"
                  description   = "Check-in date in YYYY-MM-DD format"
                  required      = true
                },
                {
                  map_block_key = "check_out_date"
                  type          = "string"
                  description   = "Check-out date in YYYY-MM-DD format"
                  required      = true
                },
                {
                  map_block_key = "guests"
                  type          = "string"
                  description   = "Number of guests (1-10)"
                  required      = true
                },
                {
                  map_block_key = "room_type"
                  type          = "string"
                  description   = "Preferred room type (optional)"
                  required      = false
                }
              ]
            },
            {
              name        = "book_hotel"
              description = "Book a selected hotel room with guest details"
              parameters = [
                {
                  map_block_key = "hotel_id"
                  type          = "string"
                  description   = "ID of the hotel to book"
                  required      = true
                },
                {
                  map_block_key = "room_type_id"
                  type          = "string"
                  description   = "ID of the room type to book"
                  required      = true
                },
                {
                  map_block_key = "check_in_date"
                  type          = "string"
                  description   = "Check-in date in YYYY-MM-DD format"
                  required      = true
                },
                {
                  map_block_key = "check_out_date"
                  type          = "string"
                  description   = "Check-out date in YYYY-MM-DD format"
                  required      = true
                },
                {
                  map_block_key = "guest_details"
                  type          = "string"
                  description   = "JSON string containing guest information and preferences"
                  required      = true
                }
              ]
            },
            {
              name        = "modify_reservation"
              description = "Modify an existing hotel reservation"
              parameters = [
                {
                  map_block_key = "reservation_id"
                  type          = "string"
                  description   = "Hotel reservation ID or booking reference to modify"
                  required      = true
                },
                {
                  map_block_key = "modifications"
                  type          = "string"
                  description   = "JSON string containing modification details"
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
      description = "Production alias for hotel booking agent"
      tags        = var.common_tags
    }
  ]

  # No collaborators for specialist agents
  collaborators = []

  # Tags
  agent_tags = merge(var.common_tags, {
    Agent = "HotelBooking"
    Role  = "Specialist"
  })
}

# Outputs
output "hotel_booking_agent_id" {
  description = "ID of the hotel booking agent"
  value       = module.hotel_booking_agent.agent_id
}

output "hotel_booking_agent_arn" {
  description = "ARN of the hotel booking agent"
  value       = module.hotel_booking_agent.agent_arn
}

output "hotel_booking_alias_arn" {
  description = "ARN of the hotel booking agent PROD alias"
  value       = module.hotel_booking_agent.agent_alias_arns["PROD"]
}

output "hotel_booking_lambda_arn" {
  description = "ARN of the hotel booking Lambda function"
  value       = aws_lambda_function.hotel_booking_lambda.arn
}