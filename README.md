# Pi Web File Server

A modern web-based file server for Raspberry Pi that allows you to browse, upload, download, and manage files through a clean web interface.

## Features

- Modern, responsive web interface with Peake Electronic Innovation branding
- Real-time system information display (CPU, Memory, Disk usage)
- Drag and drop file uploads
- File and directory operations:
  - Browse files and directories
  - Create new directories
  - Upload files (up to 5GB)
  - Download files
  - Delete files and directories
  - Move files and directories
- Bulk actions:
  - Select multiple items
  - Delete selected
  - Download selected (as zip)
  - Move selected
- Breadcrumb navigation
- Optional HTTPS support

## Installation

1. Install Python virtual environment package (on Raspberry Pi OS):
```bash
sudo apt install python3-venv
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Raspberry Pi
# or
.\venv\Scripts\activate  # On Windows
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Access the web interface by opening a browser and navigating to:
```
http://[your-pi-ip]
```

## Configuration

The server can be configured using environment variables:

- `PI_FILE_SERVER_BASE_DIR`: Base directory for file operations (default: user's home directory)
- `PI_FILE_SERVER_PORT`: Port to run the server on (default: 443)
- `PI_FILE_SERVER_DOMAIN`: Optional domain name
- `PI_FILE_SERVER_SSL_CERT`: Path to SSL certificate (optional)
- `PI_FILE_SERVER_SSL_KEY`: Path to SSL private key (optional)

## SSL Configuration (Optional)

To enable HTTPS:

1. Generate a self-signed certificate:
```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout cert/key.pem \
    -out cert/cert.pem \
    -subj "/CN=mini-server.lan"
```

2. Set the environment variables to point to your certificates:
```bash
export PI_FILE_SERVER_SSL_CERT=cert/cert.pem
export PI_FILE_SERVER_SSL_KEY=cert/key.pem
```

The server will:
- Run with HTTPS if certificates are found
- Run with HTTP if no certificates are present
- Use port 443 by default (can be changed via `PI_FILE_SERVER_PORT`)

Note: When using a self-signed certificate, your browser will show a security warning. This is normal and you can proceed by accepting the certificate.

## Running as a Service

To run the Pi File Server as a systemd service that starts automatically on boot:

1. Create a directory for shared files (optional):
```bash
mkdir ~/shared
```

2. Copy the service file to systemd:
```bash
sudo cp pi-file-server.service /etc/systemd/system/
```

3. Modify the service file if needed:
   - Update the `User` and `Group` to match your username
   - Update the `WorkingDirectory` to match your installation path
   - Update the `PI_FILE_SERVER_BASE_DIR` to your desired shared directory
   - Update the `Path` and `ExecStart` to match your virtual environment path

4. Reload systemd and enable the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-file-server
sudo systemctl start pi-file-server
```

5. Check the service status:
```bash
sudo systemctl status pi-file-server
```

6. View logs if needed:
```bash
sudo journalctl -u pi-file-server -f
```

The service will now:
- Start automatically on boot
- Restart automatically if it crashes
- Run under your user account
- Serve files from the configured base directory

## Security Notes

- The server listens on all interfaces (0.0.0.0)
- HTTPS is optional but recommended for production use
- Maximum file upload size is 5GB (configurable)
- The server is configured to start in the user's home directory by default
- All file operations are restricted to the configured base directory

## Requirements

- Python 3.6+
- Flask
- Werkzeug
- psutil
- pathlib
