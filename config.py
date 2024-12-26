import os
from pathlib import Path

# Base directory configuration
BASE_DIR = os.environ.get('PI_FILE_SERVER_BASE_DIR', str(Path.home()))  # Default to user's home directory

# Convert to Path object and resolve to absolute path
BASE_DIR = str(Path(BASE_DIR).resolve())

# Server configuration
HOST = '0.0.0.0'
PORT = int(os.environ.get('PI_FILE_SERVER_PORT', '8000'))  # Changed to 8000 default port
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB max file size

# SSL Configuration
SSL_CERT = os.environ.get('PI_FILE_SERVER_SSL_CERT', 'cert.pem')
SSL_KEY = os.environ.get('PI_FILE_SERVER_SSL_KEY', 'key.pem')

# Domain configuration
DOMAIN = os.environ.get('PI_FILE_SERVER_DOMAIN', '')
