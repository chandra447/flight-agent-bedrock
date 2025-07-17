# --- Agent Outputs ---
output "agent_id" {
  description = "ID of the created Bedrock agent"
  value       = aws_bedrockagent_agent.main.agent_id
}

output "agent_arn" {
  description = "ARN of the created Bedrock agent"
  value       = aws_bedrockagent_agent.main.agent_arn
}

output "agent_name" {
  description = "Name of the created Bedrock agent"
  value       = aws_bedrockagent_agent.main.agent_name
}

output "foundation_model" {
  description = "Foundation model used by the agent"
  value       = aws_bedrockagent_agent.main.foundation_model
}

output "agent_version" {
  description = "Version of the agent"
  value       = aws_bedrockagent_agent.main.agent_version
}

# --- IAM Role Outputs ---
output "agent_resource_role_arn" {
  description = "ARN of the IAM role used by the agent"
  value       = local.agent_resource_role_arn
}

output "agent_resource_role_name" {
  description = "Name of the IAM role created for the agent (null if using existing role)"
  value       = var.create_agent_resource_role ? aws_iam_role.agent_resource_role[0].name : null
}

# --- Action Group Outputs ---
output "action_group_ids" {
  description = "Map of action group names to their IDs"
  value = {
    for k, ag in aws_bedrockagent_agent_action_group.action_groups : 
    var.action_groups[k].name => ag.action_group_id
  }
}

output "action_group_arns" {
  description = "Map of action group names to their ARNs"
  value = {
    for k, ag in aws_bedrockagent_agent_action_group.action_groups : 
    var.action_groups[k].name => ag.action_group_arn
  }
}

# --- Agent Alias Outputs ---
output "agent_alias_ids" {
  description = "Map of agent alias names to their IDs"
  value = {
    for k, alias in aws_bedrockagent_agent_alias.agent_aliases : 
    var.agent_aliases[k].name => alias.agent_alias_id
  }
}

output "agent_alias_arns" {
  description = "Map of agent alias names to their ARNs"
  value = {
    for k, alias in aws_bedrockagent_agent_alias.agent_aliases : 
    var.agent_aliases[k].name => alias.agent_alias_arn
  }
}

# --- Collaborator Outputs ---
output "collaborator_ids" {
  description = "Map of collaborator names to their IDs"
  value = {
    for k, collab in aws_bedrockagent_agent_collaborator.collaborators : 
    var.collaborators[k].collaborator_name => collab.collaborator_id
  }
}

output "collaborator_arns" {
  description = "Map of collaborator names to their ARNs"
  value = {
    for k, collab in aws_bedrockagent_agent_collaborator.collaborators : 
    var.collaborators[k].collaborator_name => collab.collaborator_arn
  }
}