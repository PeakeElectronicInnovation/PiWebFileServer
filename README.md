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
```

4. Install the required Python packages:
```bash
pip install -r requirements.txt
```

5. (Optional) Configure environment variables:

For Linux/Mac:
```bash
# Set environment variables before running the app
export PI_FILE_SERVER_BASE_DIR=/path/to/shared/files
export PI_FILE_SERVER_PORT=8000
```

Or create a `.env` file in the project directory:
```bash
PI_FILE_SERVER_BASE_DIR=/path/to/shared/files
PI_FILE_SERVER_PORT=8000
```

Note: Environment variables must be set BEFORE running the application. You can verify they are set correctly:
- Linux/Mac: `echo $PI_FILE_SERVER_BASE_DIR`
- Windows: `echo %PI_FILE_SERVER_BASE_DIR%`

6. Run the application:
```bash
python app.py
```

7. Access the web interface:
   - Default development URL: `http://[your-pi-ip]:8000`
   - For production with HTTP: `http://[your-pi-ip]` (requires sudo or proper permissions)
   - For production with HTTPS: `https://[your-pi-ip]` (requires sudo or proper permissions)
   - Replace `[your-pi-ip]` with your Raspberry Pi's IP address
   - The IP address is shown in the console when you start the server

Note: For production use on port 80 (HTTP) or 443 (HTTPS), you'll need root privileges:
```bash
sudo python app.py
```

For development, the default port 8000 can be used without sudo.

## Configuration

The server can be configured using environment variables:

- `PI_FILE_SERVER_BASE_DIR`: Base directory for file operations (default: user's home directory)
- `PI_FILE_SERVER_PORT`: Port to run the server on (default: 8000)
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

## Running on Port 80/443 Without Sudo

There are two recommended ways to run the server on privileged ports (80/443) without sudo:

### Option 1: Port Forwarding (Recommended)

Use `iptables` to forward traffic from port 80 to a non-privileged port (e.g., 8000):

```bash
# Allow the server to bind to port 8000
python app.py &

# Forward port 80 to 8000 (requires sudo once)
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000
sudo iptables -t nat -A OUTPUT -p tcp --dport 80 -j REDIRECT --to-port 8000

# Make the rules persistent (Debian/Ubuntu)
sudo apt-get install iptables-persistent
sudo netfilter-persistent save
```

### Option 2: Capability Setting

Grant the Python binary the capability to bind to privileged ports:

```bash
# Install libcap2-bin if not already installed
sudo apt-get install libcap2-bin

# Grant capability to Python
sudo setcap 'cap_net_bind_service=+ep' $(readlink -f $(which python3))

# Now you can run directly on port 80
export PI_FILE_SERVER_PORT=80
python app.py
```

Note: The capability setting method:
- Only needs to be done once
- Applies to all Python programs run by your user
- Might need to be reapplied after Python updates
- Is more secure than running the entire application as root

### Option 3: Reverse Proxy (Production)

For production environments, it's recommended to:
1. Run the application on a high port (e.g., 8000)
2. Use Nginx or Apache as a reverse proxy
3. Have the reverse proxy handle SSL termination

Example Nginx configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

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
