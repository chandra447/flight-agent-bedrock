# --- Agent Collaborators ---
resource "aws_bedrockagent_agent_collaborator" "collaborators" {
  for_each = { for idx, collab in var.collaborators : idx => collab }
  
  agent_id                   = aws_bedrockagent_agent.main.agent_id
  agent_version              = "DRAFT"
  collaborator_name          = each.value.collaborator_name
  relay_conversation_history = each.value.relay_conversation_history
  collaboration_instruction = each.value.callabration_instruction
  
  agent_descriptor {
    alias_arn = each.value.agent_descriptor.alias_arn
  }
  
  depends_on = [aws_bedrockagent_agent.main]
}