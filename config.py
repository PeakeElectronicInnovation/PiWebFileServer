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
PORT = 5000
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
