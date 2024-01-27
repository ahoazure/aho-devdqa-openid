from .settings import *
DEBUG = True # Will be moved to external variables in Phase 2
# Configure production domain names
ALLOWED_HOSTS = [os.environ['WEBSITE_SITE_NAME'] + '.azurewebsites.net',
    'af-aho-datacapturetool-dev.azurewebsites.net',
        'dct.aho.afro.who.int'] if 'WEBSITE_SITE_NAME' in os.environ else []

# WhiteNoise configuration
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
# Add whitenoise middleware after the security middleware
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # DCT on Azure raised 404 due missing local middleware discovered 25/10/2020
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 
# # Settings for serving and uploading media into Azure Blob storage container
# AZURE_ACCOUNT_NAME = os.environ['AZURE_ACCOUNT']
# AZURE_CONTAINER = os.environ['AZURE_CONTAINER']
# AZURE_CUSTOM_DOMAIN = os.environ['AZURE_DOMAIN']
#
# #Configurations for serving static assets (CSS, JavaScript, Images)
# STATIC_LOCATION='static' #This works well as the static location
# STATICFILES_STORAGE  = 'aho_datacapturetool.azurestorage.AzureStaticStorage'
# STATIC_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{AZURE_CONTAINER}/{STATIC_LOCATION}/'
#
# # Configurations for serving and uploading files into Azure Blob storage
# DEFAULT_FILE_STORAGE = 'aho_datacapturetool.azurestorage.AzureMediaStorage'
# AZURE_BLOB_MAX_MEMORY_SIZE = os.environ['BLOB_MAX_MEMORY_SIZE']
#
# MEDIA_LOCATION='media' #This works well as the storage location
# MEDIA_URL = f'https://{AZURE_CUSTOM_DOMAIN}/{MEDIA_LOCATION}/'




"""
Use secure cookies for the session and crossite protection. An attacker could
sniff and capture an unencrypted cookies with and hijack the user’s session.
"""
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF= True
SECURE_SSL_REDIRECT=False
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# # Configure MariaDB database backends
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['DBNAME'],
        'HOST': os.environ['DBHOST'],
        'USER': os.environ['DBUSER'],
        'PASSWORD': os.environ['DBPASS'],
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'ssl': {'ca': '/home/site/cert/BaltimoreTrustDigiCertifcateCombo.pem'}
            },
    }
}
