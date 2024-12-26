# Pi Web File Server

A modern web-based file server for Raspberry Pi that allows you to browse, upload, download, and manage files through a clean web interface.

## Features

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

1. Install required system packages (on Raspberry Pi OS):
```bash
sudo apt update
sudo apt install -y python3-venv git
```

2. Clone the repository:
```bash
git clone https://github.com/PeakeElectronicInnovation/PiWebFileServer.git
cd PiWebFileServer
```

3. Create and activate a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Raspberry Pi
# or
.\venv\Scripts\activate  # On Windows
```

4. Install the required Python packages:
```bash
pip install -r requirements.txt
```

5. (Optional) Configure environment variables:
```bash
# Set the base directory for file operations (optional, defaults to home directory)
export PI_FILE_SERVER_BASE_DIR=/path/to/shared/files

# Set the port (optional, defaults to 443)
export PI_FILE_SERVER_PORT=8000

# Set SSL certificate paths (optional, for HTTPS)
export PI_FILE_SERVER_SSL_CERT=cert/cert.pem
export PI_FILE_SERVER_SSL_KEY=cert/key.pem
```

6. Run the application:
```bash
python app.py
```

7. Access the web interface:
   - If using default port (443): `https://[your-pi-ip]`
   - If using custom port: `http://[your-pi-ip]:[port]`
   - Replace `[your-pi-ip]` with your Raspberry Pi's IP address
   - The IP address is shown in the console when you start the server

Note: If you're running on port 443 (default) or 80, you'll need to run with sudo or setup proper permissions:
```bash
sudo python app.py
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

## Development Setup

If you want to contribute to the project:

1. Fork the repository on GitHub

2. Clone your fork:
```bash
git clone https://github.com/[your-username]/PiWebFileServer.git
cd PiWebFileServer
```

3. Create a new branch for your feature:
```bash
git checkout -b feature-name
```

4. Set up the development environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
.\venv\Scripts\activate  # On Windows

pip install -r requirements.txt
```

5. Run the server in development mode:
```bash
# Use a non-privileged port for development
export PI_FILE_SERVER_PORT=8000
python app.py
```

## Troubleshooting

### Permission Issues
- If you get a "Permission denied" error when running on port 443:
  - Use sudo (not recommended for development)
  - Use a port number above 1024
  - Set up proper port permissions (recommended for production)

### SSL Certificate Issues
- If you see SSL certificate warnings:
  - This is normal with self-signed certificates
  - Accept the certificate in your browser
  - For production, use a proper SSL certificate from a trusted authority

### File Permission Issues
- Ensure the application has read/write permissions for:
  - The base directory (`PI_FILE_SERVER_BASE_DIR`)
  - The SSL certificate directory (if using HTTPS)
  - The directory where the application is running

### Common Errors
- "Address already in use":
  - Another service is using the port
  - Use `sudo netstat -tulpn | grep [port]` to find what's using the port
  - Choose a different port or stop the other service

- "No such file or directory":
  - Check that all paths in environment variables are correct
  - Ensure the SSL certificates exist (if using HTTPS)
  - Verify the base directory exists and is accessible

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
