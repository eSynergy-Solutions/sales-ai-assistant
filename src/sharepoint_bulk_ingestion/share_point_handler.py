import datetime
import logging
import os

import requests
import textract


class SharePointHandler:
    """
    Handles interactions with SharePoint, including authentication, retrieving drives,
    listing items within drives, and fetching content of items.

    :param tenant_id: Tenant ID for the Azure app.
    :param client_id: Client ID for the Azure app.
    :param client_secret: Client secret for the Azure app.
    :param service_account_name: SharePoint Service Account username.
    :param service_account_password: SharePoint Service Account password.
    :param dry_run: If True, simulates actions without making actual API calls.
    """

    def __init__(self, tenant_id: str, client_id: str, client_secret: str, service_account_name: str,
                 service_account_password: str, processed_items_file: str = '.tmp_processed_items',
                 processed_drives_file: str = '.tmp_processed_drives', error_items_file: str = '.tmp_error_items',
                 dry_run: bool = False):
        """Initializes the SharePointHandler with authentication details and dry run mode."""
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.service_account_name = service_account_name
        self.service_account_password = service_account_password
        self.dry_run = dry_run
        self.token_user = None
        self.token_user_expiry = datetime.datetime.min
        self.token_admin = None
        self.token_admin_expiry = datetime.datetime.min
        self.api_call_count = 0
        self.retry_delay = 10
        self.max_retries = 3
        self.processed_items_file = processed_items_file
        self.processed_drives_file = processed_drives_file
        self.error_items_file = error_items_file

        # self.white_list_file_extensions = ['.csv', '.doc', '.docx', '.eml', '.epub', '.gif', '.jpg', '.json', '.html',
        #                                    '.mp3', '.msg', '.odt', '.ogg', '.pdf', '.png', '.pptx', '.ps', '.rtf',
        #                                    '.tiff', '.txt', '.wav', '.xlsx', '.xls']
        self.white_list_file_extensions = ['.csv', '.doc', '.docx', '.eml', '.epub', '.json', '.html', '.msg', '.odt',
                                           '.ogg', '.pdf', '.pptx', '.ps', '.rtf', '.tiff', '.txt', '.xlsx', '.xls']

    def get_api_call_count(self):
        return self.api_call_count

    def get_processed_items_file(self):
        return self.processed_items_file

    def get_processed_drives_file(self):
        return self.processed_drives_file

    def get_error_items_file(self):
        return self.error_items_file

    def get_white_list_file_extensions(self):
        return self.white_list_file_extensions

    @staticmethod
    def mark_item_as_processed(file: str, item_id: str):
        """
        Marks an item as processed by appending its ID to a file.

        :param file: The file where processed item IDs are stored.
        :param item_id: The ID of the item to mark as processed.
        """
        if not os.path.exists(file):
            logging.warning(f"The file '{file}' does not exist.")
        with open(file, 'a') as f:
            f.write(item_id + '\n')

    @staticmethod
    def has_been_processed(file: str, item_id: str):
        """
        Checks if an item has already been processed.

        :param file: The file where processed item IDs are stored.
        :param item_id: The ID of the item to check.
        :return: True if the item has been processed, False otherwise.
        """
        try:
            with open(file, 'r') as f:
                processed_items = f.read().splitlines()
            return item_id in processed_items
        except FileNotFoundError:
            return False

    @staticmethod
    def mark_item_as_error(file: str, item: str):
        """
        Marks an item as error by appending its details to a file.

        :param file: The file where processed item IDs are stored.
        :param item: The item details to mark as error.
        """
        if not os.path.exists(file):
            logging.warning(f"The file '{file}' does not exist.")
        with open(file, 'a') as f:
            f.write(item + '\n')

    @staticmethod
    def clear_processed_items_record(file: str):
        """
        Clears the record of processed items by deleting the file.

        :param file: The file where processed item IDs are stored.
        """
        if os.path.exists(file):
            os.remove(file)

    def init_auth_token(self):
        self.init_auth_token_app_only()
        self.init_auth_token_with_username_password()

    def init_auth_token_with_username_password(self):
        """
        Authenticates with the Microsoft Graph API using username and password to retrieve an access token.
        This method uses the Resource Owner Password Credential (ROPC) flow.
        Note: ROPC is not recommended for production environments due to security concerns.
        """
        if self.dry_run:
            logging.info("[Dry Run] Would initialize authentication token using username and password.")
            return

        # Ensure the URL is correct for ROPC flow; this is just an example and might need to be adjusted
        auth_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        data = {
            'grant_type': 'password',  # ROPC flow
            'client_id': self.client_id,
            'scope': 'https://graph.microsoft.com/.default',
            'username': self.service_account_name,
            'password': self.service_account_password,
        }

        # For ROPC, client secret is not typically used, but this depends on the application configuration
        if self.client_secret:
            data['client_secret'] = self.client_secret

        response = requests.post(auth_url, data=data)
        self.api_call_count += 1
        if response.status_code == 200:
            token_info = response.json()
            self.token_user = token_info['access_token']
            expires_in = token_info['expires_in']
            self.token_user_expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        else:
            raise Exception(
                f"Failed to authenticate with username and password: {response.status_code} {response.text}")

    def init_auth_token_app_only(self):
        """
        Authenticates with the Microsoft Graph API to retrieve an access token.
        The token is stored along with its expiry time.
        """
        if self.dry_run:
            logging.info("[Dry Run] Would initialize authentication token admin.")
            return
        auth_url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        response = requests.post(auth_url, data=data)
        self.api_call_count += 1
        if response.status_code == 200:
            token_info = response.json()
            self.token_admin = token_info['access_token']
            expires_in = token_info['expires_in']
            self.token_admin_expiry = datetime.datetime.now() + datetime.timedelta(seconds=expires_in)
        else:
            raise Exception(f"Failed to authenticate: {response.status_code} {response.text}")

    def check_token(self):
        """
        Checks if the current access token has expired and refreshes it by calling
        init_auth_token if necessary.
        """
        if self.dry_run:
            logging.info("[Dry Run] Would validate authentication token validity.")
            return
        if datetime.datetime.now() >= self.token_user_expiry:
            logging.info("Access token user has expired. Fetching a new token...")
            self.init_auth_token_with_username_password()
        if datetime.datetime.now() >= self.token_admin_expiry:
            logging.info("Access token admin has expired. Fetching a new token...")
            self.init_auth_token_app_only()

    def get_site_id_by_site_name(self, site_name, sharepoint_name='esynergysol.sharepoint.com'):
        self.check_token()
        if self.dry_run:
            logging.info(
                f"[Dry Run] Would fetch the site ID of the site: {site_name}")
            return "esynergysol.sharepoint.com,d042ab24-9622-4433-918f-56d48d400b1e,ee651823-c72b-4205-af34-aff0daf9bf5a"
        headers = {
            'Authorization': f'Bearer {self.token_user}',
            'Content-Type': 'application/json'
        }
        url = f'https://graph.microsoft.com/v1.0/sites/{sharepoint_name}:/sites/{site_name}?$select=id'
        response = requests.get(url, headers=headers)
        self.api_call_count += 1
        if response.status_code == 200:
            site_id_json = response.json()
            return site_id_json['id']
        else:
            raise Exception(f"Failed to get SharePoint site ID: {response.status_code} {response.text}")

    def get_drives_by_site_id(self, site_id: str):
        """
        Retrieves a list of drives within a specified SharePoint site.

        :param site_id: ID of the SharePoint site.
        :return: A list of drives within the specified site.
        """
        self.check_token()
        if self.dry_run:
            logging.info(
                f"[Dry Run] Would retrieve drives from site: {site_id}")
            return [
                {
                    'createdDateTime': '2023-10-18T14:17:38Z', 'description': '',
                    'id': 'b!JKtC0CKWM0SRj1bUjUALHiMYZe4rxwVCrzSv8Nr5v1o70sHOvnnrS5zeBpmo9GBF',
                    'lastModifiedDateTime': '2023-10-18T14:17:59Z', 'name': 'SBX - ISO Compliance Records',
                    'webUrl': 'https://esynergysol.sharepoint.com/sites/GenAI-Sandbox/'
                              'SBX%20%20ISO%20Compliance%20Records',
                    'driveType': 'documentLibrary', 'createdBy':
                    {
                        'user': {'email': 'sean@esynergy.solutions', 'id': 'dfabc68e-d286-4f14-9aec-7bf5a7c109e2',
                                 'displayName': 'Sean Admin'}
                    }, 'lastModifiedBy':
                    {
                        'user': {'email': 'sean@esynergy.solutions', 'id': 'dfabc68e-d286-4f14-9aec-7bf5a7c109e2',
                                 'displayName': 'Sean Admin'}
                    }, 'owner':
                    {
                        'group': {'email': 'GenAI-Sandbox@esynergysol.onmicrosoft.com',
                                  'id': '565ad2b6-9dbe-449f-899e-8396046cdab5', 'displayName': 'GenAI-Sandbox Owners'}
                    },
                    'quota': {'deleted': 0, 'remaining': 27315634383689, 'state': 'normal', 'total': 27487790694400,
                              'used': 172156310711}
                }
            ]
        headers = {
            'Authorization': f'Bearer {self.token_admin}',
            'Content-Type': 'application/json'
        }
        url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives'
        response = requests.get(url, headers=headers)
        self.api_call_count += 1
        if response.status_code == 200:
            drives_list = response.json()
            return drives_list['value']
        else:
            raise Exception(f"Failed to list drives: {response.status_code} {response.text}")

    def get_items_in_item_recursive(self,
                                    site_id: str,
                                    drive_id: str,
                                    item_id: str,
                                    drive_name: str,
                                    path: str = "/",
                                    items_list: list = None,
                                    max_items: int = -1):
        """
        Recursively retrieves items from a specified SharePoint site and drive, filtering by a whitelist of file 
        extensions.
        It navigates through folders starting from a given item ID or the root of the drive if the item ID is None.
        The function maintains a count of API calls and limits the number of items based on the `max_items` parameter.

        If the dry-run mode is enabled, the function simulates the retrieval process by logging the intended actions 
        without making any actual API calls or modifying data.

        :param site_id: ID of the SharePoint site.
        :param drive_id: ID of the drive from which items are retrieved.
        :param item_id: ID of the item to start the retrieval from. If None, starts from the drive root.
        :param drive_name: Name of the drive, used for item identification.
        :param path: Current path of navigation, used for constructing item paths. Defaults to root ("/").
        :param items_list: List to accumulate the retrieved items. If None, a new list is initialized.
        :param max_items: Maximum number of items to retrieve that do not belong to folders and match whitelist 
        extensions.
        The function stops when this limit is reached.
        :return: A list of dictionaries, each representing an item with its details (id, name, path, etc.),
        or an empty list if dry-run is enabled.
        """
        if items_list is None:
            items_list = []

        if self.has_been_processed(self.processed_drives_file, drive_id):
            logging.warning(f"Skipping {drive_name} drive with id: {drive_id}")
            return items_list

        if self.has_been_processed(self.processed_items_file, item_id):
            logging.warning(f"Skipping {item_id} item")
            return items_list

        self.check_token()

        if self.dry_run:
            logging.info(
                f"[Dry Run] Would retrieve items from site: {site_id}, drive: {drive_id}, starting from item: "
                f"{item_id}"
            )
            items_list.append(
                {
                    'id': '01CAE3RJCO7FOOGHJ5U5B2IA2IZ27HC2U7',
                    'name': 'Associate Contractor Forms',
                    'site_id': site_id,
                    'drive_id': drive_id,
                    'drive_name': 'SBX - ISO Compliance Records',
                    'path': '/Forms and Templates/Associate Contractor Forms',
                    'lastModifiedDateTime': '2023-10-18T14:17:58Z', 'extension': None, 'is_folder': True
                }
            )
            items_list.append(
                {
                    'id': '01CAE3RJCCYTIWX7N3SVG3SKHAKG5YR5UG',
                    'name': '01. Associate CFSA (Deliv) TEMPLATE. March 2022.docx',
                    'site_id': site_id,
                    'drive_id': drive_id,
                    'drive_name': 'SBX - ISO Compliance Records',
                    'path': '/Forms and Templates/Associate Contractor Forms/01. Associate CFSA (Deliv) TEMPLATE. '
                            'March 2022.docx',
                    'lastModifiedDateTime': '2023-10-18T14:18:01Z', 'extension': '.docx', 'is_folder': False
                }
            )
            return items_list

        headers = {
            'Authorization': f'Bearer {self.token_admin}',
            'Content-Type': 'application/json'
        }

        if max_items > 0 and (
                len(list(
                    filter(lambda d: not d['is_folder'] and d['extension'] in self.white_list_file_extensions,
                           items_list)))
                > max_items):
            return items_list

        if item_id:
            url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/children'
        else:
            # If item_id is None, list items in the drive root
            url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root/children'

        while url:
            response = requests.get(url, headers=headers)
            self.api_call_count += 1
            if response.status_code == 200:
                response_data = response.json()
                items_data = response.json()['value']
                for item in items_data:
                    item_details = self._extract_item_details(item, site_id, drive_id, drive_name, path)
                    items_list.append(item_details)
                    if item_details['is_folder']:
                        items_list.append(item_details)
                        self.get_items_in_item_recursive(site_id, drive_id, item['id'], drive_name,
                                                         item_details['path'], items_list, max_items)
                url = response_data.get('@odata.nextLink', None)
            else:
                raise Exception(f"Failed to list items for {item_id} item: {response.status_code} {response.text}")

        return items_list

    def get_item_content(self,
                         site_id: str,
                         drive_id: str,
                         item_id: str,
                         item_name: str,
                         item_path: str,
                         drive_name: str,
                         is_retry: bool):
        """
        Retrieves the content of a specified item and extracts its text.

        :param site_id: ID of the SharePoint site.
        :param drive_id: ID of the drive containing the item.
        :param item_id: ID of the item to retrieve content for.
        :param item_name: Name of the item, used for logging.
        :param item_path: Path of the item, used for logging in case of error.
        :param drive_name: Name of the drive, used for logging in case of error.
        :param is_retry: Indicates if the current attempt is a retry.
        :return: The text content of the item, if retrieval was successful; None otherwise.
        """
        if self.has_been_processed(self.processed_items_file, item_id):
            return

        self.check_token()

        if self.dry_run:
            logging.info(
                f"[Dry Run] Would retrieve content for item: {item_id} in drive: {drive_id} from site: {site_id}")
            return "This is a simulated content for dry run."
        headers = {
            'Authorization': f'Bearer {self.token_admin}',
            'Content-Type': 'application/json'
        }
        url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/items/{item_id}/content'
        retry_count = 0
        while retry_count < self.max_retries:

            response = requests.get(url, headers=headers, stream=True)
            self.api_call_count += 1
            if response.status_code == 200:

                with open(item_name, 'wb') as file:
                    file.write(response.content)

                # Process the document to extract text
                try:
                    text = textract.process(item_name)
                    logging.debug(f"{text.decode('utf-8')}")
                    return text.decode('utf-8')
                except Exception as e:
                    item_error_details = {
                        "site_id": site_id,
                        "drive_id": drive_id,
                        "item_id": item_id,
                        "drive_name": drive_name,
                        "path": item_path
                    }
                    logging.error(f"Error processing the file {item_name}: {e}\n{item_error_details}")
                    self.mark_item_as_error(self.error_items_file, str(item_error_details))
                    return None
                finally:
                    # Delete the file after processing
                    os.remove(item_name)
                    logging.debug(f"File {item_name} has been deleted.")
            elif response.status_code == 403:
                item_error_details = {
                    "site_id": site_id,
                    "drive_id": drive_id,
                    "item_id": item_id,
                    "drive_name": drive_name,
                    "path": item_path
                }
                logging.warning(f"Access denied for {item_id} item {item_error_details}:\n "
                                f"{response.status_code} {response.text}"
                                )
                return None
            else:
                retry_count = + 1
                item_error_details = {
                    "site_id": site_id,
                    "drive_id": drive_id,
                    "item_id": item_id,
                    "drive_name": drive_name,
                    "path": item_path
                }
                logging.error(
                    f"Failed to get item content for {item_id} item {item_error_details}:\n "
                    f"{response.status_code} {response.text}"
                )
                if not is_retry:
                    self.mark_item_as_error(self.error_items_file, str(item_error_details))
        return None

    @staticmethod
    def _extract_item_details(item: dict, site_id: str, drive_id: str, drive_name: str, path: str):
        """
        Extracts and organizes details from a SharePoint item for internal use.

        :param item: The SharePoint item from which details are extracted.
        :param site_id: ID of the SharePoint site.
        :param drive_id: ID of the drive containing the item.
        :param drive_name: Name of the drive.
        :param path: Current navigation path.
        :return: A dictionary containing extracted item details.
        """
        item_path = f"{path}/{item['name']}" if path != "/" else f"/{item['name']}"
        is_folder = 'folder' in item
        item_details = {
            'id': item['id'],
            'name': item['name'],
            'site_id': site_id,
            'drive_id': drive_id,
            'drive_name': drive_name,
            'path': item_path,
            'lastModifiedDateTime': item.get('lastModifiedDateTime'),
            'is_folder': is_folder
        }
        if not is_folder:
            item_details['extension'] = os.path.splitext(item['name'])[1]
        return item_details
