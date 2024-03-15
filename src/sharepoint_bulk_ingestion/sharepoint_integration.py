import argparse
import datetime
import logging
import os
from typing import Optional, Dict

import boto3
from astra_db_handler import AstraDBHandler
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from blob_storage_handler import BlobStorageHandler
from langchain_community.embeddings import BedrockEmbeddings
from share_point_handler import SharePointHandler

drive_white_list = ["SBX - Bid Respository"]


def parse_args():
    """
    Parses command-line arguments.

    :return: Namespace with parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Running Sharepoint Integration")
    parser.add_argument("-cl", "--console-log", dest="console_log_level", default="info",
                        help="Providing console logging level. Example --console-log 'debug', default = 'info'")
    parser.add_argument("-fl", "--file-log", dest="file_log_level", default="debug",
                        help="Providing file logging level. Example --file-log 'debug', default = 'debug'")
    parser.add_argument("-lf", "--log-file", dest="log_file", default=".tmp_sharepoint_integration.log",
                        help="Providing logging file name, default = '.tmp_sharepoint_integration.log'")
    parser.add_argument("--max-drives", dest="max_drives", help="Maximum number of drives to process",
                        required=False, default=-1)
    parser.add_argument("--max-items", dest="max_items", help="Maximum number of Items to process",
                        required=False, default=-1)
    parser.add_argument("--bulk-item-count", dest="bulk_item_count", help="Maximum number of Items to process",
                        required=False, default=10)
    parser.add_argument("-dry", "--dry-run", action="store_true", help="Templating engine dry run")
    return parser.parse_args()


def setup_logging(console_log_level: str, file_log_level: str, file_name: str):
    """
    Configures separate logging levels for console and file logging.

    :param console_log_level: The logging level for the console as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    :param file_log_level: The logging level for the file as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    :param file_name: The name of the file to log to.
    """
    console_numeric_level = getattr(logging, console_log_level.upper(), None)
    file_numeric_level = getattr(logging, file_log_level.upper(), None)

    if not isinstance(console_numeric_level, int):
        raise ValueError(f"Invalid console log level: {console_log_level}")
    if not isinstance(file_numeric_level, int):
        raise ValueError(f"Invalid file log level: {file_log_level}")

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(min(console_numeric_level, file_numeric_level))  # Set to the lower of the two levels

    # Create console handler with the specific log level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_numeric_level)

    # Create file handler with the specific log level
    file_handler = logging.FileHandler(file_name)
    file_handler.setLevel(file_numeric_level)

    # Create formatter and add it to both handlers
    formatter = logging.Formatter("%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add both handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def process_all_sharepoint_files_by_site_name(sharepoint_handler: SharePointHandler,
                                              astra_db_text_handler: AstraDBHandler,
                                              site_name: str,
                                              max_drives: int,
                                              max_items: int,
                                              bulk_item_count: int):
    # Authenticate with SharePoint
    sharepoint_handler.init_auth_token_with_username_password()

    site_id = sharepoint_handler.get_site_id_by_site_name(site_name)

    # Get drives by site ID
    drives = sharepoint_handler.get_drives_by_site_id(site_id)
    drives_to_process = sorted(drives[:max_drives if max_drives > 0 else len(drives)], key=lambda x: x['name'])

    inserted_db_document_count = 0
    inserted_item_count = 0
    total_processed_items = 0
    # Initialize the combined chunks list
    combined_chunks = []

    for drive_idx, drive in enumerate(drives_to_process):
        logging.info(f"Total API calls made so far: {sharepoint_handler.get_api_call_count()}")

        logging.info(f"Processing drive: {drive['name']}")

        drive_name = drive['name']
        if drive_name not in drive_white_list:
            continue

        # For each drive, get items recursively
        items = sharepoint_handler.get_items_in_item_recursive(site_id, drive['id'], None, drive['name'],
                                                               max_items=max_items)

        logging.info(f"Total API calls made so far: {sharepoint_handler.get_api_call_count()}")
        items_to_process = list(
            filter(
                lambda d: not d['is_folder'] and d['extension'] in sharepoint_handler.get_white_list_file_extensions(),
                items)
        )
        items_to_process = items_to_process[:max_items if max_items > 0 else len(items_to_process)]
        logging.info(f"{len(items_to_process)} files found.")

        for item_idx, item in enumerate(items_to_process):
            logging.info(f"Processing item: {item['name']}. {item_idx}/{len(items_to_process)} item | "
                         f"{drive_idx}/{len(drives_to_process)} drive.")
            # Get item content
            content = sharepoint_handler.get_item_content(site_id, drive['id'], item['id'], item['name'],
                                                          item['path'], drive['name'], is_retry=False)

            # Split content into chunks and process each chunk
            if content:
                metadata = {
                    "id": item['id'],
                    "name": item['name'],
                    "site_id": site_id,
                    "path": item['path'],
                    "drive_name": item['drive_name'],
                }
                chunks = astra_db_text_handler.recursive_character_doc_splitter(content, metadata)

                # Accumulate chunks
                combined_chunks.extend(chunks)

                # Check if the bulk item count is reached or it's the last item of the last drive
                if total_processed_items % bulk_item_count == 0 or (
                        item_idx == len(items_to_process) - 1 and drive_idx == len(drives_to_process) - 1):
                    # Ingest chunks with embeddings into AstraDB
                    inserted_ids = astra_db_text_handler.ingest_chunks_with_embeddings_to_astra_db(combined_chunks)
                    inserted_db_document_count += len(inserted_ids)
                    inserted_item_count += bulk_item_count
                    logging.info(f"Inserted {inserted_item_count} documents")
                    logging.info(f"Inserted {inserted_db_document_count} chunks")

                    logging.info(f"total_processed_items: {total_processed_items} documents")

                    # Reset combined chunks list after ingestion
                    combined_chunks = []

                total_processed_items += 1

                sharepoint_handler.mark_item_as_processed(sharepoint_handler.get_processed_items_file(), item['id'])

        sharepoint_handler.mark_item_as_processed(sharepoint_handler.get_processed_drives_file(), drive['id'])
        sharepoint_handler.clear_processed_items_record(sharepoint_handler.get_processed_items_file())

    logging.info(f"{inserted_item_count} items inserted and {inserted_db_document_count} documents have been "
                 f"inserted in the vector DB")
    logging.info(f"{total_processed_items} items in total")


def get_env_vars(required_env_vars: list) -> Optional[Dict[str, str]]:
    """
    Check and return environment variables, logging an error for any missing ones.

    :param required_env_vars: A list of strings representing the required environment variable names.
    :return: A dictionary of environment variable names and their values if all are present, None otherwise.
    """
    missing_env_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_env_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_env_vars)}")
        return None
    return {var: os.environ.get(var) for var in required_env_vars}


def get_secrets_from_key_vault(secret_client: SecretClient, secrets: list) -> Dict[str, str]:
    """
    Fetch and return secrets from Azure Key Vault.

    :param secret_client: An instance of SecretClient configured with vault URL and credentials.
    :param secrets: A list of strings representing the secret names to fetch.
    :return: A dictionary of secret names and their values.
    """
    return {secret: secret_client.get_secret(secret).value for secret in secrets}


def initialize_handlers(secure: bool, collection_name: str, dry_run: bool,
                        key_vault_secrets: Optional[Dict[str, str]] = None) -> (
        Optional[SharePointHandler], Optional[AstraDBHandler]):
    blob_storage_handler = None
    if secure:
        # Assuming key_vault_secrets is not None if secure is True
        # Setup AWS credentials
        logging.info(f"Setting up AWS to use Bedrock")
        os.environ['AWS_ACCESS_KEY_ID'] = key_vault_secrets['aws-access-key-id']
        os.environ['AWS_SECRET_ACCESS_KEY'] = key_vault_secrets['aws-secret-access-key']

        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        embeddings = BedrockEmbeddings(client=bedrock,
                                       model_id='amazon.titan-embed-text-v1')

        logging.info(f"Setting up sharepoint_handler and astra_db_text_handler")
        sharepoint_handler = SharePointHandler(
            tenant_id=key_vault_secrets['sharepoint-tenant-id'],
            client_id=key_vault_secrets['sharepoint-client-id'],
            client_secret=key_vault_secrets['sharepoint-client-secret'],
            service_account_name=key_vault_secrets['sharepoint-service-account-name'],
            service_account_password=key_vault_secrets['sharepoint-service-account-password'],
            dry_run=dry_run
        )
        astra_db_text_handler = AstraDBHandler(
            astra_url=os.environ['ASTRA_DB_API_ENDPOINT'],
            astra_application_token=key_vault_secrets['astra-db-application-token'],
            astra_keyspace=os.environ['ASTRA_DB_KEYSPACE'],
            collection_name=collection_name,
            embeddings=embeddings,
            dry_run=dry_run
        )

        blob_storage_handler = BlobStorageHandler(connection_string=key_vault_secrets['blob-connection-string'],
                                                  container_name=os.environ['BLOB_CONTAINER_NAME'])
        blob_storage_handler.initialize_and_retrieve_temp_files()

    else:
        env_vars = get_env_vars([
            'SHAREPOINT_TENANT_ID', 'SHAREPOINT_CLIENT_ID', 'SHAREPOINT_CLIENT_SECRET',
            'SHAREPOINT_SERVICE_ACCOUNT_NAME', 'SHAREPOINT_SERVICE_ACCOUNT_PASSWORD',
            'ASTRA_DB_API_ENDPOINT', 'ASTRA_DB_APPLICATION_TOKEN'
        ])
        if env_vars is None:
            return None, None

        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        embeddings = BedrockEmbeddings(client=bedrock,
                                       model_id='amazon.titan-embed-text-v1')

        sharepoint_handler = SharePointHandler(
            tenant_id=os.environ['SHAREPOINT_TENANT_ID'],
            client_id=os.environ['SHAREPOINT_CLIENT_ID'],
            client_secret=os.environ['SHAREPOINT_CLIENT_SECRET'],
            service_account_name=os.environ.get('SHAREPOINT_SERVICE_ACCOUNT_NAME'),
            service_account_password=os.environ.get('SHAREPOINT_SERVICE_ACCOUNT_PASSWORD'),
            dry_run=dry_run
        )
        astra_db_text_handler = AstraDBHandler(
            astra_url=env_vars['ASTRA_DB_API_ENDPOINT'],
            astra_application_token=env_vars['ASTRA_DB_APPLICATION_TOKEN'],
            astra_keyspace=os.environ['ASTRA_DB_KEYSPACE'],
            collection_name=collection_name,
            embeddings=embeddings,
            dry_run=dry_run
        )

    return sharepoint_handler, astra_db_text_handler, blob_storage_handler


def main():
    """
    Main entry point of the script. Orchestrates the process of fetching SharePoint files, processing them,
    and ingesting them into AstraDB.

    :return: None
    """
    args = parse_args()
    setup_logging(args.console_log_level, args.file_log_level, args.log_file)

    secure_str = os.getenv("SECURE", "False")

    # Convert the string to a boolean value
    if secure_str.lower() == 'true':
        secure = True
    elif secure_str.lower() == 'false':
        secure = False
    else:
        # Raise an error if SECURE is not "True" or "False"
        raise ValueError(f"SECURE environment variable must be 'True' or 'False', but found '{secure_str}'")
    logging.info(f"Running script with secure mode {'enabled' if secure else 'disabled'}")

    # Key Vault integration
    key_vault_secrets = None
    if secure:
        key_vault_vars = get_env_vars(
            ['BLOB_CONTAINER_NAME', 'KEY_VAULT_URL', 'SHAREPOINT_SITE_NAME', 'SHAREPOINT_COLLECTION_NAME',
             'ASTRA_DB_API_ENDPOINT', 'ASTRA_DB_KEYSPACE'])
        if key_vault_vars is None:
            return
        credential = DefaultAzureCredential()
        secret_client = SecretClient(vault_url=key_vault_vars['KEY_VAULT_URL'], credential=credential)
        key_vault_secrets = get_secrets_from_key_vault(secret_client, [
            'aws-access-key-id', 'aws-secret-access-key',
            'sharepoint-tenant-id', 'sharepoint-client-id', 'sharepoint-client-secret',
            'sharepoint-service-account-name', 'sharepoint-service-account-password',
            'astra-db-application-token', 'blob-connection-string'
        ])
    else:
        if get_env_vars([
            'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',
            'SHAREPOINT_TENANT_ID', 'SHAREPOINT_CLIENT_ID', 'SHAREPOINT_CLIENT_SECRET',
            'SHAREPOINT_SERVICE_ACCOUNT_NAME', 'SHAREPOINT_SERVICE_ACCOUNT_PASSWORD', 'SHAREPOINT_SITE_NAME',
            'SHAREPOINT_COLLECTION_NAME', 'ASTRA_DB_API_ENDPOINT', 'ASTRA_DB_APPLICATION_TOKEN',
            'ASTRA_DB_KEYSPACE'
        ]) is None:
            return

    collection_name = os.environ['SHAREPOINT_COLLECTION_NAME']

    sharepoint_handler, astra_db_text_handler, blob_storage_handler = initialize_handlers(secure, collection_name,
                                                                                          args.dry_run,
                                                                                          key_vault_secrets if secure
                                                                                          else None)
    if not sharepoint_handler or not astra_db_text_handler:
        return

    logging.info("Starting SharePoint processing...")
    start_time = datetime.datetime.now()

    try:
        process_all_sharepoint_files_by_site_name(
            sharepoint_handler, astra_db_text_handler,
            os.environ['SHAREPOINT_SITE_NAME'],
            int(args.max_drives), int(args.max_items), int(args.bulk_item_count)
        )
    except Exception as e:
        logging.error(f"Error processing files in site {os.environ['SHAREPOINT_SITE_NAME']}: \n {e}")
    finally:
        if secure:
            logging.info(f"Pushing tmp files to Azure Storage")
            blob_storage_handler.save_temp_files_to_azure_storage()

    # Uncomment the following line if you want to reprocess drives after a successful run
    # sharepoint_handler.clear_processed_items_record(sharepoint_handler.get_processed_drives_file())

    end_time = datetime.datetime.now()
    logging.info(f"Finished processing. Total time: {end_time - start_time}")


if __name__ == "__main__":
    main()
