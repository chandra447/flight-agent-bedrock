variable "agent_name" {
  description = "Name of the Bedrock agent"
  type        = string
  validation {
    condition     = length(var.agent_name) > 0 && length(var.agent_name) < 100
    error_message = "Agent name must be between 1 and 100 characters"
  }
  nullable = false
}

variable "agent_instruction" {
  description = "Instruction for the Bedrock agent"
  type        = string
  validation {
    condition     = length(var.agent_instruction) > 0
    error_message = "Instruction cannot be empty"
  }
  nullable = false
}

variable "agent_description" {
  description = "Description of the Bedrock agent"
  type        = string
  default     = ""
}

# Making the foundation model default to sonnet as this is what we have requested
variable "foundation_model" {
  description = "Foundation model to use for the agent"
  type        = string
  default     = "mistral.mistral-7b-instruct-v0:2"
}

variable "idle_session_ttl_in_seconds" {
  description = "The number of seconds that a Bedrock agent session is maintained. (60-3600 seconds)"
  type        = number
  default     = null
}

variable "agent_collaboration" {
  description = "Agents Collaboration role"
  type        = string
  nullable    = true
  default     = null

}

variable "prepare_agent" {
  description = "Whether to prepare the agent after creation or modification"
  type        = bool
  default     = true
}

variable "memory_configuration" {
  description = "Configuration for the Bedrock agent's memory. Set to null to disable memory, or provide a map with 'enabled' (bool) and 'storage_days' (number, optional)."
  type = object({
    enabled      = bool
    storage_days = optional(number)
  })
  default = null
}

variable "guardrail_configuration" {
  description = "Details about the guardrail associated with the agent"
  type = object({
    guardrail_identifier = string
    guardrail_version    = number
  })
  default = null
}

variable "customer_encryption_key_arn" {
  description = "The ARN of the KMS key used to encrypt the agent's data."
  type        = string
  default     = null
}

variable "agent_tags" {
  description = "A map of tags to apply to the Bedrock Agent resource"
  type        = map(string)
  default     = {}
}



#==================================
# Agent Aliases
#==================================
variable "agent_aliases" {
  description = "A list of agent alias configurations."
  type = list(object({
    name        = string
    description = optional(string)
    routing_configuration = optional(object({
      agent_version          = string
      provisioned_throughput = optional(string)
    }))
    tags = optional(map(string), {})
  }))
  default = []
}

#==================================
# Action group
#==================================
variable "action_groups" {
  description = "A list of action group configurations to associate with the agent."
  type = list(object({
    name               = string
    description        = optional(string)
    action_group_state = optional(string, "ENABLED") # Default to ENABLED
    action_group_executor = object({
      custom_control = optional(string)
      lambda         = optional(string)
    })
    api_schema = optional(object({
      payload = optional(string)
      s3 = optional(object({
        s3_bucket_name = optional(string)
        s3_object_key  = optional(string)
      }))
    }))
    function_schema = optional(object({
      member_functions = optional(object({
        functions = optional(list(object({
          name        = string
          description = optional(string)
          parameters = optional(list(object({
            map_block_key = string
            type          = string
            description   = optional(string)
            required      = optional(bool)
          })))
        })))
      }))
    }))
  }))
  default = [] # Default to an empty list to make action groups optional

  validation {
    # Each action group must provide ONLY one of 'api_schema' or 'function_schema'.
    condition = alltrue([
      for ag in var.action_groups :
      (ag.api_schema != null && ag.function_schema == null) || (ag.api_schema == null && ag.function_schema != null)
    ])
    error_message = "Each action group must provide ONLY one of 'api_schema' or 'function_schema'."
  }
}

#==================================
# Agent Collaborators
#==================================
variable "collaborators" {
  description = "A list of collaborator configurations to associate with the agent."
  type = list(object({
    collaborator_name          = string
    instruction                = string
    agent_collaboration        = optional(string, "DISABLED")        # SUPERVISOR, SUPERVISOR_ROUTER, DISABLED
    relay_conversation_history = optional(string, "TO_COLLABORATOR") # TO_COLLABORATOR, TO_COLLABORATOR_AND_CUSTOMER
    agent_descriptor = object({
      alias_arn = string # The agent alias ARN of the collaborator agent
    })
  }))
  default = []

  validation {
    condition = alltrue([
      for collab in var.collaborators : contains([
        "SUPERVISOR",
        "SUPERVISOR_ROUTER",
        "DISABLED"
      ], collab.agent_collaboration)
    ])
    error_message = "Agent collaboration must be 'SUPERVISOR', 'SUPERVISOR_ROUTER', or 'DISABLED'."
  }

  validation {
    condition = alltrue([
      for collab in var.collaborators : contains([
        "TO_COLLABORATOR",
        "TO_COLLABORATOR_AND_CUSTOMER"
      ], collab.relay_conversation_history)
    ])
    error_message = "Relay conversation history must be 'TO_COLLABORATOR' or 'TO_COLLABORATOR_AND_CUSTOMER'."
  }

  validation {
    condition = alltrue([
      for collab in var.collaborators : length(collab.collaborator_name) > 0 && length(collab.collaborator_name) <= 100
    ])
    error_message = "Collaborator name must be between 1 and 100 characters."
  }

  validation {
    condition = alltrue([
      for collab in var.collaborators : length(collab.instruction) > 0
    ])
    error_message = "Collaborator instruction cannot be empty."
  }
}

#==================================
# Flags to check auto-creation of iam roles
#==================================
variable "create_agent_resource_role" {
  description = "Whether to create the IAM role for the Bedrock agent. If false, provide existing agent_resource_role_arn"
  type        = bool
  default     = true
}

variable "existing_agent_resource_role_arn" {
  description = "The ARN of an existing IAM role the Bedrock Agent"
  type        = string
  default     = null
}

# Note: Collaborators variable is already defined above
