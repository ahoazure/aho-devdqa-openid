from storages.backends.azure_storage import AzureStorage
import os
import dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Add .env variables before assiging the values to the SECRET_KEY variable
dotenv_file = os.path.join(BASE_DIR, ".env")
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

class AzureMediaStorage(AzureStorage):
    account_name = os.environ['AZURE_ACCOUNT']
    account_key = os.environ['STORAGE_ACCOUNT_KEY']
    azure_container = os.environ['AZURE_CONTAINER']
    expiration_secs = None

class AzureStaticStorage(AzureStorage):
    account_name = os.environ['AZURE_ACCOUNT']
    account_key = os.environ['STORAGE_ACCOUNT_KEY']
    azure_container = os.environ['AZURE_CONTAINER']
    expiration_secs = None
