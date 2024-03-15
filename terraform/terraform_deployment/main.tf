#terraform {
#  backend "azurerm" {
#    resource_group_name  = "sandbox"
#    storage_account_name = "agrsalescopilotterraform"
#    container_name       = "deploymenttfstate"
#    key                  = "terraform.tfstate"
#  }
#}

terraform {
  backend "azurerm" {
    resource_group_name  = "Main_Resources"
    storage_account_name = "salescopilotterraform"
    container_name       = "deploymentbatchtfstate"
    key                  = "terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
  skip_provider_registration = true
}

resource "null_resource" "recreate_trigger" {
  triggers = {
    always_change = "${timestamp()}"
  }
}

data "azurerm_user_assigned_identity" "identity" {
  name                = local.managed_identity_name
  resource_group_name = local.resource_group_name
}

data "azurerm_log_analytics_workspace" "log_analytics_workspace" {
  name                = local.log_analytics_workspace_name
  resource_group_name = local.resource_group_name
}

data "azurerm_key_vault" "key_vault" {
  name                = local.key_vault_name
  resource_group_name = local.resource_group_name
}

data "azurerm_container_registry" "container_registry" {
  name                = local.container_registry_name
  resource_group_name = local.resource_group_name
}

resource "azurerm_container_group" "container_group" {
  name                = local.container_group_name
  location            = local.resource_group_location
  resource_group_name = local.resource_group_name
  os_type             = "Linux"
  restart_policy      = "Never"

  identity {
    type         = local.managed_identity_type
    identity_ids = [data.azurerm_user_assigned_identity.identity.id]
  }

  image_registry_credential {
    server                    = data.azurerm_container_registry.container_registry.login_server
    user_assigned_identity_id = data.azurerm_user_assigned_identity.identity.id
  }

  container {
    name   = local.container_group_container_name
    image  = "${data.azurerm_container_registry.container_registry.login_server}/${local.container_instance_image_name}:${local.container_instance_image_tag}"
    cpu    = local.container_instance_cpu
    memory = local.container_instance_memory

    ports {
      port     = 80
      protocol = "TCP"
    }

    environment_variables = {
      "SECURE"                     = local.container_instance_secure
      "KEY_VAULT_URL"              = data.azurerm_key_vault.key_vault.vault_uri
      "SHAREPOINT_SITE_NAME"       = local.container_instance_sharepoint_site_name
      "SHAREPOINT_COLLECTION_NAME" = local.container_instance_sharepoint_collection_name
      "ASTRA_DB_API_ENDPOINT"      = local.container_instance_astra_db_api_endpoint
      "ASTRA_DB_KEYSPACE"          = local.container_instance_astra_db_keyspace
      "BLOB_CONTAINER_NAME"        = local.blob_container_name
    }
  }

  diagnostics {
    log_analytics {
      workspace_id  = data.azurerm_log_analytics_workspace.log_analytics_workspace.workspace_id
      workspace_key = data.azurerm_log_analytics_workspace.log_analytics_workspace.primary_shared_key
    }
  }

  lifecycle {
    replace_triggered_by = [
      null_resource.recreate_trigger.id,
    ]
    create_before_destroy = false
  }

  depends_on = [null_resource.recreate_trigger]

}


