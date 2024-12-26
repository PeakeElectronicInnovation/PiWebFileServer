import os
from pathlib import Path

# Base directory configuration
BASE_DIR = str(Path.home())  # Default to user's home directory

# You can override this by setting an environment variable
if os.environ.get('PI_FILE_SERVER_BASE_DIR'):
    BASE_DIR = os.environ.get('PI_FILE_SERVER_BASE_DIR')

# Convert to Path object and resolve to absolute path
BASE_DIR = str(Path(BASE_DIR).resolve())

# Server configuration
HOST = '0.0.0.0'
PORT = 443  # Changed to HTTPS default port
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# SSL Configuration
SSL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ssl')
SSL_CERT = os.path.join(SSL_DIR, 'fullchain.pem')
SSL_KEY = os.path.join(SSL_DIR, 'privkey.pem')

# Domain configuration
DOMAIN = os.environ.get('PI_FILE_SERVER_DOMAIN', 'mini-server.lan')
