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
http://[your-pi-ip]:5000
```

## SSL Configuration

To enable HTTPS with a self-signed certificate:

1. Create SSL directory and generate self-signed certificate:
```bash
# Create SSL directory
sudo mkdir -p /home/admin/PiWebFileServer/ssl

# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /home/admin/PiWebFileServer/ssl/privkey.pem \
    -out /home/admin/PiWebFileServer/ssl/fullchain.pem \
    -subj "/CN=mini-server.lan"

# Set correct permissions
sudo chown -R admin:admin /home/admin/PiWebFileServer/ssl
sudo chmod 700 /home/admin/PiWebFileServer/ssl
sudo chmod 600 /home/admin/PiWebFileServer/ssl/*.pem
```

2. Restart the service:
```bash
sudo systemctl restart pi-file-server
```

The server will now:
- Run on port 443 (standard HTTPS port)
- Automatically redirect HTTP to HTTPS
- Use self-signed SSL certificate

Note: When accessing the server for the first time, your browser will show a security warning because the certificate is self-signed. This is normal and you can proceed by accepting the certificate. The connection will still be encrypted, just not verified by a trusted certificate authority.

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

- By default, the server runs on port 5000 and listens on all interfaces (0.0.0.0)
- The server is configured to start in the user's home directory
- Maximum file upload size is set to 16MB (can be adjusted in app.py)
- It's recommended to run this behind a reverse proxy with HTTPS in production

## Requirements

- Python 3.6+
- Flask
- Werkzeug
- pathlib
