#!/bin/bash

# Exit on error
set -e

echo "Starting Pi File Server installation..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Prompt for base directory
DEFAULT_BASE_DIR="/var/lib/pifileserver"
read -p "Enter base directory for file storage [$DEFAULT_BASE_DIR]: " BASE_DIR
BASE_DIR=${BASE_DIR:-$DEFAULT_BASE_DIR}

# Expand the path to absolute
BASE_DIR=$(realpath -m "$BASE_DIR")

# Confirm directory
echo "Files will be stored in: $BASE_DIR"
read -p "Continue? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! $REPLY == "" ]]; then
    echo "Installation cancelled"
    exit 1
fi

# Install system dependencies
echo "Installing system dependencies..."
apt-get update
apt-get install -y python3-venv python3-pip

# Create service user if it doesn't exist
echo "Setting up service user..."
if ! id -u pifileserver &>/dev/null; then
    useradd -r -s /bin/false pifileserver
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create base directory if it doesn't exist
echo "Setting up directories..."
mkdir -p "$BASE_DIR"
chown pifileserver:pifileserver "$BASE_DIR"

# Create environment file
echo "Creating environment configuration..."
cat > /etc/pifileserver.env << EOL
# Pi File Server Configuration
PI_FILE_SERVER_BASE_DIR=$BASE_DIR
PI_FILE_SERVER_PORT=8000
# Uncomment and set these for HTTPS
#PI_FILE_SERVER_SSL_CERT=/path/to/cert.pem
#PI_FILE_SERVER_SSL_KEY=/path/to/key.pem
EOL

# Set up systemd service
echo "Setting up systemd service..."
cat > /etc/systemd/system/pifileserver.service << EOL
[Unit]
Description=Pi File Server
After=network.target

[Service]
Type=simple
User=pifileserver
Group=pifileserver
EnvironmentFile=/etc/pifileserver.env
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Set correct permissions
echo "Setting permissions..."
chown -R pifileserver:pifileserver "$SCRIPT_DIR"
chmod 644 /etc/systemd/system/pifileserver.service
chmod 644 /etc/pifileserver.env

# Reload systemd and start service
echo "Starting service..."
systemctl daemon-reload
systemctl enable pifileserver
systemctl start pifileserver

echo "Installation complete!"
echo "The Pi File Server is now running at http://localhost:8000"
echo "Files are stored in: $BASE_DIR"
echo "To check the service status: systemctl status pifileserver"
echo "To view logs: journalctl -u pifileserver"
echo "Configuration file: /etc/pifileserver.env"
