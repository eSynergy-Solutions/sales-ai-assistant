locals {
  resource_group_name            = "Main_Resources"
  resource_group_location        = "UK South"
  tenant_id                      = "fa28c433-c46a-42cd-98b2-c8f7db5b20aa"
  managed_identity_name          = "sales-copilot-identity"
  key_vault_name                 = "genai-sandbox-key-vault"
  container_registry_name        = "genaisandboxacr"
  log_analytics_workspace_name   = "genai-sales-copilot-log-analytics-workspace"
  container_group_name           = "genai-sales-copilot-containergroup"
  container_group_container_name = "genai-sales-copilot-container"

  managed_identity_type         = "UserAssigned"
  container_instance_image_name = "sharepoint_bulk_ingestion"
  container_instance_image_tag  = "latest"
  container_instance_cpu        = "1"
  container_instance_memory     = "1"

  container_instance_secure                     = "True"
  container_instance_sharepoint_site_name       = "GenAI-Sandbox"
  container_instance_sharepoint_collection_name = "sandbox_sharepoint_docs"
  container_instance_astra_db_api_endpoint      = "https://e9d2e8b7-38ca-4891-a20b-41d01f37b5d8-westus3.apps.astra.datastax.com"
  container_instance_astra_db_keyspace          = "dev"
  blob_container_name                           = "statusfiles"
}