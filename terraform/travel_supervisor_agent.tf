# Travel Supervisor Agent Terraform Configuration
# Creates the supervisor agent with Lambda action groups and proper IAM roles

# Lambda function for supervisor agent operations
resource "aws_lambda_function" "travel_supervisor_lambda" {
  filename         = data.archive_file.travel_supervisor_lambda_zip.output_path
  function_name    = "travel-supervisor-agent-lambda"
  role            = aws_iam_role.travel_supervisor_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 512

  source_code_hash = data.archive_file.travel_supervisor_lambda_zip.output_base64sha256

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket_name
      S3_DB_KEY = var.s3_db_key
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.travel_supervisor_lambda_basic,
    aws_iam_role_policy_attachment.travel_supervisor_lambda_s3,
    aws_cloudwatch_log_group.travel_supervisor_lambda_logs,
  ]

  tags = var.common_tags
}

# Create Lambda deployment package
data "archive_file" "travel_supervisor_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/../lambda_packages/travel_supervisor_lambda.zip"
  
  source {
    content = templatefile("${path.module}/../lambda_functions/travel_supervisor_agent/lambda_function.py", {
      # Template variables if needed
    })
    filename = "lambda_function.py"
  }
  
  source {
    content  = file("${path.module}/../database/db_utils.py")
    filename = "db_utils.py"
  }
}

# IAM role for Lambda function
resource "aws_iam_role" "travel_supervisor_lambda_role" {
  name = "travel-supervisor-lambda-role"

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
resource "aws_iam_role_policy_attachment" "travel_supervisor_lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.travel_supervisor_lambda_role.name
}

# S3 access policy for database
resource "aws_iam_role_policy_attachment" "travel_supervisor_lambda_s3" {
  policy_arn = aws_iam_policy.lambda_s3_access.arn
  role       = aws_iam_role.travel_supervisor_lambda_role.name
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "travel_supervisor_lambda_logs" {
  name              = "/aws/lambda/travel-supervisor-agent-lambda"
  retention_in_days = 14
  tags              = var.common_tags
}

# Lambda permission for Bedrock agent
resource "aws_lambda_permission" "travel_supervisor_bedrock_invoke" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.travel_supervisor_lambda.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = module.travel_supervisor_agent.agent_arn
}

# Travel Supervisor Agent using auto-agents module
module "travel_supervisor_agent" {
  source = "../modules/auto-agents"

  # Basic agent configuration
  agent_name        = "travel-supervisor-agent"
  agent_description = "Travel Supervisor Agent that coordinates complex travel booking requests and manages collaboration with specialist travel agents"
  foundation_model  = var.foundation_model
  agent_instruction = file("${path.module}/../agent_instructions/travel_supervisor_instruction.txt")

  # Supervisor configuration
  agent_collaboration = "SUPERVISOR"
  prepare_agent      = true

  # Memory configuration
  memory_configuration = {
    enabled      = true
    storage_days = 30
  }

  # Action groups for supervisor operations
  action_groups = [
    {
      name        = "supervisor-operations"
      description = "Core supervisor operations for request analysis and coordination"
      action_group_executor = {
        lambda = aws_lambda_function.travel_supervisor_lambda.arn
      }
      function_schema = {
        member_functions = {
          functions = [
            {
              name        = "analyze_request"
              description = "Analyze incoming travel requests and determine required services and specialists"
              parameters = [
                {
                  map_block_key = "user_request"
                  type          = "string"
                  description   = "The travel request from the user"
                  required      = true
                },
                {
                  map_block_key = "request_type"
                  type          = "string"
                  description   = "Type of travel request (business, leisure, emergency, etc.)"
                  required      = false
                }
              ]
            },
            {
              name        = "coordinate_specialists"
              description = "Coordinate with specialist agents for comprehensive travel planning"
              parameters = [
                {
                  map_block_key = "specialist_responses"
                  type          = "string"
                  description   = "JSON string containing responses from specialist agents"
                  required      = true
                },
                {
                  map_block_key = "request_context"
                  type          = "string"
                  description   = "JSON string with context information about the original request"
                  required      = true
                }
              ]
            },
            {
              name        = "consolidate_response"
              description = "Consolidate and synthesize responses from multiple travel specialists"
              parameters = [
                {
                  map_block_key = "multiple_agent_responses"
                  type          = "string"
                  description   = "JSON string containing responses from multiple agents"
                  required      = true
                },
                {
                  map_block_key = "user_context"
                  type          = "string"
                  description   = "JSON string with user preferences and context"
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
      description = "Production alias for travel supervisor agent"
      tags        = var.common_tags
    }
  ]

  # Collaborators will be configured after other agents are created
  collaborators = []

  # Tags
  agent_tags = merge(var.common_tags, {
    Agent = "TravelSupervisor"
    Role  = "Supervisor"
  })
}

# Outputs
output "travel_supervisor_agent_id" {
  description = "ID of the travel supervisor agent"
  value       = module.travel_supervisor_agent.agent_id
}

output "travel_supervisor_agent_arn" {
  description = "ARN of the travel supervisor agent"
  value       = module.travel_supervisor_agent.agent_arn
}

output "travel_supervisor_alias_arn" {
  description = "ARN of the travel supervisor agent PROD alias"
  value       = module.travel_supervisor_agent.agent_alias_arns["PROD"]
}

output "travel_supervisor_lambda_arn" {
  description = "ARN of the travel supervisor Lambda function"
  value       = aws_lambda_function.travel_supervisor_lambda.arn
}