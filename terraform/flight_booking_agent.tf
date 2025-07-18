# Flight Booking Agent Terraform Configuration
# Creates the flight booking specialist agent with Lambda action groups

# Lambda function for flight booking operations
resource "aws_lambda_function" "flight_booking_lambda" {
  filename         = data.archive_file.flight_booking_lambda_zip.output_path
  function_name    = "flight-booking-agent-lambda"
  role            = aws_iam_role.flight_booking_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  source_code_hash = data.archive_file.flight_booking_lambda_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket_name
      S3_DB_KEY = var.s3_db_key
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.flight_booking_lambda_basic,
    aws_iam_role_policy_attachment.flight_booking_lambda_s3,
    aws_cloudwatch_log_group.flight_booking_lambda_logs,
  ]

  tags = var.common_tags
}

# Create Lambda deployment package
data "archive_file" "flight_booking_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/../lambda_packages/flight_booking_lambda.zip"
  
  source {
    content = templatefile("${path.module}/../lambda_functions/flight_booking_agent/lambda_function.py", {
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
resource "aws_iam_role" "flight_booking_lambda_role" {
  name = "flight-booking-lambda-role"

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
resource "aws_iam_role_policy_attachment" "flight_booking_lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.flight_booking_lambda_role.name
}

# S3 access policy for database
resource "aws_iam_role_policy_attachment" "flight_booking_lambda_s3" {
  policy_arn = aws_iam_policy.lambda_s3_access.arn
  role       = aws_iam_role.flight_booking_lambda_role.name
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "flight_booking_lambda_logs" {
  name              = "/aws/lambda/flight-booking-agent-lambda"
  retention_in_days = var.log_retention_days
  tags              = var.common_tags
}

# Lambda permission for Bedrock agent
resource "aws_lambda_permission" "flight_booking_bedrock_invoke" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.flight_booking_lambda.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = module.flight_booking_agent.agent_arn
}

# Flight Booking Agent using auto-agents module
module "flight_booking_agent" {
  source = "../modules/auto-agents"

  # Basic agent configuration
  agent_name        = "flight-booking-agent"
  agent_description = "Flight Booking Agent specialized in flight searches, airline bookings, and air travel coordination"
  foundation_model  = var.foundation_model
  agent_instruction = file("${path.module}/../agent_instructions/flight_booking_instruction.txt")

  # Collaborator configuration (not supervisor)
  agent_collaboration = null
  prepare_agent      = true

  # Memory configuration
  memory_configuration = {
    enabled      = true
    storage_days = 7
  }

  # Action groups for flight operations
  action_groups = [
    {
      name        = "flight-operations"
      description = "Flight search, booking, and cancellation operations"
      action_group_executor = {
        lambda = aws_lambda_function.flight_booking_lambda.arn
      }
      function_schema = {
        member_functions = {
          functions = [
            {
              name        = "search_flights"
              description = "Search for available flights based on travel criteria"
              parameters = [
                {
                  map_block_key = "origin"
                  type          = "string"
                  description   = "Origin airport code or city name"
                  required      = true
                },
                {
                  map_block_key = "destination"
                  type          = "string"
                  description   = "Destination airport code or city name"
                  required      = true
                },
                {
                  map_block_key = "departure_date"
                  type          = "string"
                  description   = "Departure date in YYYY-MM-DD format"
                  required      = true
                },
                {
                  map_block_key = "return_date"
                  type          = "string"
                  description   = "Return date in YYYY-MM-DD format (optional for one-way)"
                  required      = false
                },
                {
                  map_block_key = "passengers"
                  type          = "string"
                  description   = "Number of passengers (1-9)"
                  required      = true
                }
              ]
            },
            {
              name        = "book_flight"
              description = "Book a selected flight with passenger details"
              parameters = [
                {
                  map_block_key = "flight_id"
                  type          = "string"
                  description   = "ID of the flight to book"
                  required      = true
                },
                {
                  map_block_key = "passenger_details"
                  type          = "string"
                  description   = "JSON string containing passenger information and preferences"
                  required      = true
                }
              ]
            },
            {
              name        = "cancel_flight"
              description = "Cancel a flight booking and process refund"
              parameters = [
                {
                  map_block_key = "booking_reference"
                  type          = "string"
                  description   = "Flight booking reference number to cancel"
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
      description = "Production alias for flight booking agent"
      tags        = var.common_tags
    }
  ]

  # No collaborators for specialist agents
  collaborators = []

  # Tags
  agent_tags = merge(var.common_tags, {
    Agent = "FlightBooking"
    Role  = "Specialist"
  })
}

# Outputs
output "flight_booking_agent_id" {
  description = "ID of the flight booking agent"
  value       = module.flight_booking_agent.agent_id
}

output "flight_booking_agent_arn" {
  description = "ARN of the flight booking agent"
  value       = module.flight_booking_agent.agent_arn
}

output "flight_booking_alias_arn" {
  description = "ARN of the flight booking agent PROD alias"
  value       = module.flight_booking_agent.agent_alias_arns["PROD"]
}

output "flight_booking_lambda_arn" {
  description = "ARN of the flight booking Lambda function"
  value       = aws_lambda_function.flight_booking_lambda.arn
}