locals {
  resource_group_name          = "Main_Resources"
  resource_group_location      = "UK South"
  tenant_id                    = "fa28c433-c46a-42cd-98b2-c8f7db5b20aa"
  managed_identity_name        = "sales-copilot-identity"
  key_vault_name               = "genai-sandbox-key-vault"
  container_registry_name      = "genaisandboxacr"
  log_analytics_workspace_name = "genai-sales-copilot-log-analytics-workspace"
}