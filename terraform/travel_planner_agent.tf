# Travel Planner Agent Terraform Configuration
# Creates the travel planning specialist agent with Lambda action groups

# Lambda function for travel planning operations
resource "aws_lambda_function" "travel_planner_lambda" {
  filename         = data.archive_file.travel_planner_lambda_zip.output_path
  function_name    = "travel-planner-agent-lambda"
  role            = aws_iam_role.travel_planner_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = var.lambda_timeout
  memory_size     = var.lambda_memory_size

  source_code_hash = data.archive_file.travel_planner_lambda_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket_name
      S3_DB_KEY = var.s3_db_key
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.travel_planner_lambda_basic,
    aws_iam_role_policy_attachment.travel_planner_lambda_s3,
    aws_cloudwatch_log_group.travel_planner_lambda_logs,
  ]

  tags = var.common_tags
}

# Create Lambda deployment package
data "archive_file" "travel_planner_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/../lambda_packages/travel_planner_lambda.zip"
  
  source {
    content = templatefile("${path.module}/../lambda_functions/travel_planner_agent/lambda_function.py", {
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
resource "aws_iam_role" "travel_planner_lambda_role" {
  name = "travel-planner-lambda-role"

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
resource "aws_iam_role_policy_attachment" "travel_planner_lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.travel_planner_lambda_role.name
}

# S3 access policy for database
resource "aws_iam_role_policy_attachment" "travel_planner_lambda_s3" {
  policy_arn = aws_iam_policy.lambda_s3_access.arn
  role       = aws_iam_role.travel_planner_lambda_role.name
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "travel_planner_lambda_logs" {
  name              = "/aws/lambda/travel-planner-agent-lambda"
  retention_in_days = var.log_retention_days
  tags              = var.common_tags
}

# Lambda permission for Bedrock agent
resource "aws_lambda_permission" "travel_planner_bedrock_invoke" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.travel_planner_lambda.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = module.travel_planner_agent.agent_arn
}

# Travel Planner Agent using auto-agents module
module "travel_planner_agent" {
  source = "../modules/auto-agents"

  # Basic agent configuration
  agent_name        = "travel-planner-agent"
  agent_description = "Travel Planner Agent specialized in destination planning, itinerary creation, and comprehensive travel advisory services"
  foundation_model  = var.foundation_model
  agent_instruction = file("${path.module}/../agent_instructions/travel_planner_instruction.txt")

  # Collaborator configuration (not supervisor)
  agent_collaboration = null
  prepare_agent      = true

  # Memory configuration
  memory_configuration = {
    enabled      = true
    storage_days = 14
  }

  # Action groups for travel planning operations
  action_groups = [
    {
      name        = "travel-planning-operations"
      description = "Itinerary creation, destination information, and travel advisory operations"
      action_group_executor = {
        lambda = aws_lambda_function.travel_planner_lambda.arn
      }
      function_schema = {
        member_functions = {
          functions = [
            {
              name        = "create_itinerary"
              description = "Create a detailed travel itinerary based on preferences and constraints"
              parameters = [
                {
                  map_block_key = "destination"
                  type          = "string"
                  description   = "Destination name or city for the itinerary"
                  required      = true
                },
                {
                  map_block_key = "duration"
                  type          = "string"
                  description   = "Number of days for the trip (1-30)"
                  required      = true
                },
                {
                  map_block_key = "interests"
                  type          = "string"
                  description   = "Comma-separated list of interests (culture, food, nature, adventure, etc.)"
                  required      = false
                },
                {
                  map_block_key = "budget"
                  type          = "string"
                  description   = "Budget range or specific amount for the trip"
                  required      = false
                }
              ]
            },
            {
              name        = "get_destination_info"
              description = "Get comprehensive information about a specific destination"
              parameters = [
                {
                  map_block_key = "destination"
                  type          = "string"
                  description   = "Destination name or city to get information about"
                  required      = true
                },
                {
                  map_block_key = "info_type"
                  type          = "string"
                  description   = "Type of information requested (general, attractions, weather, culture, etc.)"
                  required      = false
                }
              ]
            },
            {
              name        = "get_travel_advisories"
              description = "Get current travel advisories and requirements for a destination"
              parameters = [
                {
                  map_block_key = "destination"
                  type          = "string"
                  description   = "Destination name or country to get travel advisories for"
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
      description = "Production alias for travel planner agent"
      tags        = var.common_tags
    }
  ]

  # No collaborators for specialist agents
  collaborators = []

  # Tags
  agent_tags = merge(var.common_tags, {
    Agent = "TravelPlanner"
    Role  = "Specialist"
  })
}

# Outputs
output "travel_planner_agent_id" {
  description = "ID of the travel planner agent"
  value       = module.travel_planner_agent.agent_id
}

output "travel_planner_agent_arn" {
  description = "ARN of the travel planner agent"
  value       = module.travel_planner_agent.agent_arn
}

output "travel_planner_alias_arn" {
  description = "ARN of the travel planner agent PROD alias"
  value       = module.travel_planner_agent.agent_alias_arns["PROD"]
}

output "travel_planner_lambda_arn" {
  description = "ARN of the travel planner Lambda function"
  value       = aws_lambda_function.travel_planner_lambda.arn
}