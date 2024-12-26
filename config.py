import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Base directory for file operations
BASE_DIR = os.environ.get('PI_FILE_SERVER_BASE_DIR')
if not BASE_DIR:
    BASE_DIR = os.path.expanduser('~')
    logger.warning(f"PI_FILE_SERVER_BASE_DIR not set, using default: {BASE_DIR}")
else:
    logger.info(f"Using configured base directory: {BASE_DIR}")

# Convert to absolute path
BASE_DIR = os.path.abspath(BASE_DIR)

# Domain name (optional)
DOMAIN = os.environ.get('PI_FILE_SERVER_DOMAIN', '')

# Port number (default to 8000 for development)
PORT = int(os.environ.get('PI_FILE_SERVER_PORT', '8000'))

# SSL certificate paths (optional)
SSL_CERT = os.environ.get('PI_FILE_SERVER_SSL_CERT', 'cert.pem')
SSL_KEY = os.environ.get('PI_FILE_SERVER_SSL_KEY', 'key.pem')

# Maximum content length for file uploads (5GB)
MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024

# Log all configuration on startup
logger.info("Configuration loaded:")
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"PORT: {PORT}")
logger.info(f"DOMAIN: {DOMAIN}")
logger.info(f"SSL_CERT: {SSL_CERT}")
logger.info(f"SSL_KEY: {SSL_KEY}")
logger.info(f"MAX_CONTENT_LENGTH: {MAX_CONTENT_LENGTH / (1024*1024*1024):.1f}GB")
