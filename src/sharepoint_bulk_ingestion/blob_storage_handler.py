from azure.storage.blob import BlobServiceClient
import logging


class BlobStorageHandler:
    def __init__(self, connection_string: str, container_name: str, temp_files: list = None):
        self.connection_string = connection_string
        self.container_name = container_name
        self.temp_files = temp_files if temp_files else ['.tmp_processed_items', '.tmp_processed_drives',
                                                         '.tmp_error_items', '.tmp_sharepoint_integration.log']
        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    def initialize_and_retrieve_temp_files(self):
        for file_name in self.temp_files:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
            try:
                with open(file_name, "wb") as download_file:
                    download_file.write(blob_client.download_blob().readall())
                    logging.info(f"File {file_name} downloaded from Azure Blob Storage.")
            except Exception as e:
                logging.info(f"File {file_name} does not exist in Azure Blob Storage. Initializing...")
                with open(file_name, "wb") as new_file:
                    new_file.write(b'')  # Create an empty file
                blob_client.upload_blob(b'', overwrite=True)

    def save_temp_files_to_azure_storage(self):
        logging.info(f"Saving files {self.temp_files} to Azure Blob Storage.")
        for file_name in self.temp_files:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=file_name)
            blob_client.delete_blob()
            with open(file_name, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
