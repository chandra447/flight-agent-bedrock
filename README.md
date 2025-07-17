# Auto-Agents Terraform Module

A comprehensive Terraform module for creating AWS Bedrock agents with action groups, collaborators, and proper IAM configurations.

## Features

- 🤖 **Bedrock Agent creation and configuration**
- 👥 **Agent Collaborators with supervision roles**
- 🔧 **Action Groups** (OpenAPI and Function schema support)
- 🔐 **Flexible IAM role management** (create new or use existing)
- 🎯 **Agent collaboration modes** (SUPERVISOR, SUPERVISOR_ROUTER, DISABLED)
- 🏷️ **Agent Aliases** for versioning and routing
- 🧠 **Memory Configuration** for session management
- 🛡️ **Guardrail Configuration** for safety
- 🚀 **CI/CD ready** with GitHub Actions

## Module Structure

```
modules/auto-agents/
├── main.tf              # Main Bedrock agent resource
├── variables.tf         # All input variables
├── outputs.tf          # All outputs
├── iam.tf              # IAM roles and policies
├── actiongroups.tf     # Action group resources
└── collaborators.tf    # Agent collaborator resources
```

## Usage

### Basic Usage

```hcl
module "auto_agents" {
  source = "./modules/auto-agents"
  
  agent_name        = "my-bedrock-agent"
  agent_description = "My custom Bedrock agent"
  agent_instruction = "You are a helpful AI assistant."
  foundation_model  = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  
  agent_tags = {
    Environment = "production"
    Team        = "ai-platform"
  }
}
```

### Complete Example with All Features

```hcl
module "comprehensive_agent" {
  source = "./modules/auto-agents"
  
  # Basic Configuration
  agent_name                     = "comprehensive-bedrock-agent"
  agent_description              = "A comprehensive Bedrock agent with all features"
  agent_instruction              = file("./instructions/agent_instruction.txt")
  foundation_model               = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  idle_session_ttl_in_seconds    = 1800
  prepare_agent                  = true
  agent_collaboration            = "SUPERVISOR"
  
  # Memory Configuration
  memory_configuration = {
    enabled      = true
    storage_days = 30
  }
  
  # Guardrail Configuration
  guardrail_configuration = {
    guardrail_identifier = "your-guardrail-id"
    guardrail_version    = 1
  }
  
  # Action Groups
  action_groups = [{
    name        = "jira-operations"
    description = "Handle JIRA ticket operations"
    action_group_executor = {
      lambda = "arn:aws:lambda:us-east-1:123456789012:function:jira-handler"
    }
    function_schema = {
      member_functions = {
        functions = [{
          name        = "get_ticket_details"
          description = "Get JIRA ticket information"
          parameters = [{
            map_block_key = "ticket_key"
            type          = "string"
            description   = "The JIRA ticket key"
            required      = true
          }]
        }]
      }
    }
  }]
  
  # Agent Aliases
  agent_aliases = [{
    name        = "production_v1"
    description = "Production alias for the agent"
  }]
  
  # Collaborators
  collaborators = [{
    collaborator_name          = "specialist-agent"
    instruction                = "You are a specialist agent that provides expert analysis."
    agent_collaboration        = "SUPERVISOR"
    relay_conversation_history = "TO_COLLABORATOR"
    agent_descriptor = {
      alias_arn = "arn:aws:bedrock:us-east-1:123456789012:agent-alias/SPEC123/ALIAS456"
    }
  }]
  
  agent_tags = {
    Environment = "production"
    Project     = "ai-platform"
    Agent       = "comprehensive"
  }
}
```

### Using Custom IAM Role

```hcl
# Create your own IAM role
resource "aws_iam_role" "custom_bedrock_role" {
  name = "my-custom-bedrock-role"
  
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
      }
    }]
  })
}

module "auto_agents" {
  source = "./modules/auto-agents"
  
  agent_name        = "my-bedrock-agent"
  agent_instruction = "You are a helpful AI assistant."
  
  # Use custom role instead of creating new one
  create_agent_resource_role      = false
  existing_agent_resource_role_arn = aws_iam_role.custom_bedrock_role.arn
}
```

## Agent Collaboration

Collaborators can have different collaboration roles:

- **SUPERVISOR**: Agent acts as a supervisor for the collaborator
- **SUPERVISOR_ROUTER**: Agent acts as a supervisor router
- **DISABLED**: No special collaboration role (default)

```hcl
collaborators = [
  {
    collaborator_name          = "specialist-agent"
    instruction                = "You are a specialist agent that provides expert analysis."
    agent_collaboration        = "SUPERVISOR"
    relay_conversation_history = "TO_COLLABORATOR"
    agent_descriptor = {
      alias_arn = "arn:aws:bedrock:us-east-1:123456789012:agent-alias/SPEC123/ALIAS456"
    }
  },
  {
    collaborator_name          = "router-agent"
    instruction                = "You are a router agent that directs conversations."
    agent_collaboration        = "SUPERVISOR_ROUTER"
    relay_conversation_history = "TO_COLLABORATOR_AND_CUSTOMER"
    agent_descriptor = {
      alias_arn = "arn:aws:bedrock:us-east-1:123456789012:agent-alias/ROUTE789/ALIAS012"
    }
  }
]
```

## Action Groups

Action groups support both OpenAPI and Function schemas:

### Function Schema Example
```hcl
action_groups = [{
  name        = "jira-operations"
  description = "Handle JIRA ticket operations"
  action_group_executor = {
    lambda = "arn:aws:lambda:us-east-1:123456789012:function:jira-handler"
  }
  function_schema = {
    member_functions = {
      functions = [{
        name        = "get_ticket_details"
        description = "Get comprehensive ticket information"
        parameters = [{
          map_block_key = "ticket_key"
          type          = "string"
          description   = "The JIRA ticket key"
          required      = true
        }]
      }]
    }
  }
}]
```

### OpenAPI Schema Example
```hcl
action_groups = [{
  name        = "api-operations"
  description = "Handle API operations"
  action_group_executor = {
    lambda = "arn:aws:lambda:us-east-1:123456789012:function:api-handler"
  }
  api_schema = {
    payload = file("./schemas/openapi.json")
  }
}]
```

## Examples

The module includes several comprehensive examples:

- **`examples/supervisor-agent/`** - Basic supervisor agent with JIRA integration
- **`examples/supervisor-with-collaborators/`** - Multi-agent collaboration setup
- **`examples/complete/`** - Complete example with all features
- **`examples/custom-role/`** - Using custom IAM roles

## Outputs

The module provides comprehensive outputs:

```hcl
# Agent Information
output "agent_id" { }
output "agent_arn" { }
output "agent_name" { }
output "foundation_model" { }

# IAM Role Information
output "agent_resource_role_arn" { }
output "agent_resource_role_name" { }

# Action Groups
output "action_group_ids" { }
output "action_group_arns" { }

# Agent Aliases
output "agent_alias_ids" { }
output "agent_alias_arns" { }

# Collaborators
output "collaborator_ids" { }
output "collaborator_arns" { }
```

## CI/CD Integration

Trigger deployments by including `tf deploy` in your commit message on feature branches.