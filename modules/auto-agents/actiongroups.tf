# --- Action Groups ---
resource "aws_bedrockagent_agent_action_group" "action_groups" {
  for_each = { for idx, ag in var.action_groups : idx => ag }
  
  action_group_name  = each.value.name
  agent_id          = aws_bedrockagent_agent.main.agent_id
  agent_version     = "DRAFT"
  description       = each.value.description
  action_group_state = each.value.action_group_state
  
  # Action Group Executor
  dynamic "action_group_executor" {
    for_each = each.value.action_group_executor.lambda != null || each.value.action_group_executor.custom_control != null ? [1] : []
    content {
      lambda         = each.value.action_group_executor.lambda
      custom_control = each.value.action_group_executor.custom_control
    }
  }
  
  # API Schema
  dynamic "api_schema" {
    for_each = each.value.api_schema != null ? [1] : []
    content {
      payload = each.value.api_schema.payload
      
      dynamic "s3" {
        for_each = each.value.api_schema.s3 != null ? [1] : []
        content {
          s3_bucket_name = each.value.api_schema.s3.s3_bucket_name
          s3_object_key  = each.value.api_schema.s3.s3_object_key
        }
      }
    }
  }
  
  # Function Schema
  dynamic "function_schema" {
    for_each = each.value.function_schema != null ? [1] : []
    content {
      dynamic "member_functions" {
        for_each = each.value.function_schema.member_functions != null ? [1] : []
        content {
          dynamic "functions" {
            for_each = each.value.function_schema.member_functions.functions != null ? each.value.function_schema.member_functions.functions : []
            content {
              name        = functions.value.name
              description = functions.value.description
              
              dynamic "parameters" {
                for_each = functions.value.parameters != null ? functions.value.parameters : []
                content {
                  map_block_key = parameters.value.map_block_key
                  type          = parameters.value.type
                  description   = parameters.value.description
                  required      = parameters.value.required
                }
              }
            }
          }
        }
      }
    }
  }
  
  depends_on = [aws_bedrockagent_agent.main]
}