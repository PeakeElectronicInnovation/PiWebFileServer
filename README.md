# Pi Web File Server

A modern web-based file server for Raspberry Pi that allows you to browse, upload, download, and delete files through a clean web interface.

## Features

- Modern, responsive web interface
- Drag and drop file uploads
- File and directory browsing
- File downloads
- File and empty directory deletion
- Breadcrumb navigation

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the web interface by opening a browser and navigating to:
```
http://[your-pi-ip]:5000
```

## Security Notes

- By default, the server runs on port 5000 and listens on all interfaces (0.0.0.0)
- The server is configured to start in the user's home directory
- Maximum file upload size is set to 16MB (can be adjusted in app.py)
- It's recommended to run this behind a reverse proxy with HTTPS in production

## Requirements

- Python 3.6+
- Flask
- Werkzeug
- pathlib
