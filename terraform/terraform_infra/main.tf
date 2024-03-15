#terraform {
#  backend "azurerm" {
#    resource_group_name  = "sandbox"
#    storage_account_name = "agrsalescopilotterraform"
#    container_name       = "tfstate"
#    key                  = "terraform.tfstate"
#  }
#}

terraform {
  backend "azurerm" {
    resource_group_name  = "Main_Resources"
    storage_account_name = "salescopilotterraform"
    container_name       = "infratfstate"
    key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

resource "azurerm_user_assigned_identity" "identity" {
  resource_group_name = local.resource_group_name
  location            = local.resource_group_location
  name                = local.managed_identity_name
}

resource "azurerm_key_vault" "key_vault" {
  name                      = local.key_vault_name
  location                  = local.resource_group_location
  resource_group_name       = local.resource_group_name
  tenant_id                 = local.tenant_id
  sku_name                  = "standard"
  enable_rbac_authorization = true

  depends_on = [azurerm_user_assigned_identity.identity]
}

resource "azurerm_role_assignment" "azurerm_key_vault_secret_user" {
  scope                = azurerm_key_vault.key_vault.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.identity.principal_id

  depends_on = [azurerm_key_vault.key_vault, azurerm_user_assigned_identity.identity]
}

resource "azurerm_container_registry" "container_registry" {
  name                = local.container_registry_name
  resource_group_name = local.resource_group_name
  location            = local.resource_group_location
  sku                 = "Basic"
  admin_enabled       = false

  depends_on = [azurerm_user_assigned_identity.identity]

}

resource "azurerm_role_assignment" "acr_pull" {
  scope                = azurerm_container_registry.container_registry.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.identity.principal_id

  depends_on = [azurerm_container_registry.container_registry, azurerm_user_assigned_identity.identity]
}

resource "azurerm_log_analytics_workspace" "log_analytics_workspace" {
  name                = local.log_analytics_workspace_name
  location            = local.resource_group_location
  resource_group_name = local.resource_group_name
  sku                 = "PerGB2018"

  depends_on = [azurerm_user_assigned_identity.identity]
}

resource "azurerm_role_assignment" "log_analytics_contributor" {
  scope                = azurerm_log_analytics_workspace.log_analytics_workspace.id
  role_definition_name = "Log Analytics Contributor"
  principal_id         = azurerm_user_assigned_identity.identity.principal_id

  depends_on = [azurerm_log_analytics_workspace.log_analytics_workspace, azurerm_user_assigned_identity.identity]
}


