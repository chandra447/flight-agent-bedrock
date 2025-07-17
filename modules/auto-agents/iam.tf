# --- Data Sources ---
data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

# --- IAM Role for Bedrock Agent Resource ---
resource "aws_iam_role" "agent_resource_role" {
  count = var.create_agent_resource_role ? 1 : 0
  name  = "${var.agent_name}-bedrock-agent-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "bedrock.amazonaws.com"
      }
      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
        }
        ArnLike = {
          "aws:SourceArn" = "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
        }
      }
    }]
  })
  
  tags = var.agent_tags
}

# --- Inline Policy for Bedrock Foundation Model Invocation ---
resource "aws_iam_role_policy" "agent_foundation_model_policy" {
  count = var.create_agent_resource_role ? 1 : 0
  name  = "${var.agent_name}-agent-foundation-model-policy"
  role  = aws_iam_role.agent_resource_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "bedrock:InvokeModel"
      Resource = "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}::foundation-model/${var.foundation_model}"
    }]
  })
}

# --- Inline Policy for CloudWatch Logs ---
resource "aws_iam_role_policy" "agent_cloudwatch_logs_policy" {
  count = var.create_agent_resource_role ? 1 : 0
  name  = "${var.agent_name}-agent-cloudwatch-logs-policy"
  role  = aws_iam_role.agent_resource_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock/*"
    }]
  })
}

# --- Collaboration Policy (Only created when collaborators are defined) ---
resource "aws_iam_role_policy" "collaboration_policy" {
  count = var.create_agent_resource_role && length(var.collaborators) > 0 ? 1 : 0
  name  = "${var.agent_name}-collaboration-policy"
  role  = aws_iam_role.agent_resource_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:GetAgent",
          "bedrock:GetAgentAlias",
          "bedrock:InvokeAgent",
          "bedrock:ListAgentAliases"
        ]
        Resource = [
          "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*",
          "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent-alias/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:GetAgentCollaborator",
          "bedrock:ListAgentCollaborators"
        ]
        Resource = [
          "arn:${data.aws_partition.current.partition}:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
        ]
      }
    ]
  })
}

# --- Lambda Invocation Policy ---
resource "aws_iam_role_policy" "agent_lambda_invokation_policy" {
  count = var.create_agent_resource_role && length(var.action_groups) > 0 ? 1 : 0
  name  = "${var.agent_name}-agent-bedrock-lambda-invoke-policy"
  role  = aws_iam_role.agent_resource_role[0].id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "lambda:InvokeFunction"
      Resource = [
        for ag in var.action_groups : ag.action_group_executor.lambda 
        if ag.action_group_executor.lambda != null && ag.action_group_executor.lambda != ""
      ]
    }]
  })
}

# --- Locals ---
locals {
  agent_resource_role_arn = var.create_agent_resource_role ? aws_iam_role.agent_resource_role[0].arn : var.existing_agent_resource_role_arn
}