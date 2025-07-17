terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

# --- Bedrock Agent ---
resource "aws_bedrockagent_agent" "main" {
  agent_name                     = var.agent_name
  agent_resource_role_arn        = local.agent_resource_role_arn
  description                    = var.agent_description
  foundation_model               = var.foundation_model
  instruction                    = var.agent_instruction
  idle_session_ttl_in_seconds    = var.idle_session_ttl_in_seconds
  prepare_agent                  = var.prepare_agent
  agent_collaboration            = var.agent_collaboration
  customer_encryption_key_arn    = var.customer_encryption_key_arn
  
  # Memory Configuration
  dynamic "memory_configuration" {
    for_each = var.memory_configuration != null ? [var.memory_configuration] : []
    content {
      enabled_memory_types = memory_configuration.value.enabled ? ["SESSION_SUMMARY"] : []
      storage_days        = memory_configuration.value.storage_days
    }
  }
  
  # Guardrail Configuration
  dynamic "guardrail_configuration" {
    for_each = var.guardrail_configuration != null ? [var.guardrail_configuration] : []
    content {
      guardrail_identifier = guardrail_configuration.value.guardrail_identifier
      guardrail_version    = guardrail_configuration.value.guardrail_version
    }
  }
  
  tags = var.agent_tags
}

# Note: Action Groups are now in actiongroups.tf

# --- Agent Aliases ---
resource "aws_bedrockagent_agent_alias" "agent_aliases" {
  for_each = { for idx, alias in var.agent_aliases : idx => alias }
  
  agent_alias_name = each.value.name
  agent_id         = aws_bedrockagent_agent.main.agent_id
  description      = each.value.description

  dynamic "routing_configuration" {
    for_each = each.value.routing_configuration != null ? [each.value.routing_configuration] : []
    content {
      agent_version          = routing_configuration.value.agent_version
      provisioned_throughput = routing_configuration.value.provisioned_throughput
    }
  }

  tags = each.value.tags

  depends_on = [aws_bedrockagent_agent.main]
}

# Note: Agent Collaborators are now in collaborators.tf