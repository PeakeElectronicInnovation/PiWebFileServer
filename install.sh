#!/bin/bash

# Exit on error
set -e

# Get the actual user who ran sudo (not root)
ACTUAL_USER=${SUDO_USER:-$USER}
ACTUAL_HOME=$(getent passwd "$ACTUAL_USER" | cut -d: -f6)

# Installation paths
INSTALL_DIR="$ACTUAL_HOME/.local/share/pifileserver"
CONFIG_DIR="$ACTUAL_HOME/.config/pifileserver"
SERVICE_FILE="$ACTUAL_HOME/.config/systemd/user/pifileserver.service"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to uninstall
uninstall() {
    echo "Uninstalling Pi File Server..."
    
    # Stop and disable service
    echo "Stopping service..."
    systemctl --user --machine="$ACTUAL_USER@.host" stop pifileserver 2>/dev/null || true
    systemctl --user --machine="$ACTUAL_USER@.host" disable pifileserver 2>/dev/null || true
    
    # Remove service file
    echo "Removing service file..."
    rm -f "$SERVICE_FILE"
    
    # Remove application files
    echo "Removing application files..."
    rm -rf "$INSTALL_DIR"
    
    # Remove configuration
    echo "Removing configuration files..."
    rm -rf "$CONFIG_DIR"
    
    # Reload systemd
    systemctl --user --machine="$ACTUAL_USER@.host" daemon-reload
    
    echo "Uninstallation complete!"
    echo "Note: Your data directory has not been removed."
    echo "To completely remove all data, manually delete your configured data directory."
}

# Function to install
install() {
    echo "Starting Pi File Server installation..."
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then 
        echo "Please run as root (use sudo)"
        exit 1
    fi

    # Get the directory where the script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

    # Prompt for base directory
    DEFAULT_BASE_DIR="$ACTUAL_HOME/Documents"
    read -p "Enter base directory for file storage [$DEFAULT_BASE_DIR]: " BASE_DIR
    BASE_DIR=${BASE_DIR:-$DEFAULT_BASE_DIR}

    # Expand ~ and $HOME to actual home directory
    BASE_DIR="${BASE_DIR/#\~/$ACTUAL_HOME}"
    BASE_DIR="${BASE_DIR/\$HOME/$ACTUAL_HOME}"

    # Convert to absolute path and remove any trailing slashes
    BASE_DIR=$(realpath -m "$BASE_DIR")

    # Confirm directory
    echo "Files will be stored in: $BASE_DIR"
    read -p "Continue? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! $REPLY == "" ]]; then
        echo "Installation cancelled"
        exit 1
    fi

    # Check and install dependencies
    echo "Checking system dependencies..."
    
    # Only run apt-get update and install if python3-venv or python3-pip is missing
    if ! command_exists python3 || ! python3 -c "import venv" >/dev/null 2>&1 || ! command_exists pip3; then
        echo "Installing missing Python dependencies..."
        # Try apt-get update, but don't fail if it errors
        apt-get update || true
        # Install packages, trying different methods
        if ! apt-get install -y python3-venv python3-pip; then
            echo "Failed to install via apt-get. Checking if packages are already installed..."
            if ! command_exists python3 || ! python3 -c "import venv" >/dev/null 2>&1 || ! command_exists pip3; then
                echo "Error: Required packages (python3-venv, python3-pip) could not be installed."
                echo "Please install them manually and run this script again."
                exit 1
            fi
        fi
    else
        echo "Python dependencies already installed."
    fi

    # Create and configure installation directory
    echo "Setting up installation directory..."
    mkdir -p "$INSTALL_DIR"
    cp -r "$SCRIPT_DIR"/* "$INSTALL_DIR/"
    cd "$INSTALL_DIR"

    # Create virtual environment
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate

    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
    deactivate

    # Create base directory if it doesn't exist
    echo "Setting up storage directory..."
    mkdir -p "$BASE_DIR"

    # Create environment file
    echo "Creating environment configuration..."
    mkdir -p "$CONFIG_DIR"
    ENV_FILE="$CONFIG_DIR/config"

    cat > "$ENV_FILE" << EOL
# Pi File Server Configuration
PI_FILE_SERVER_BASE_DIR=$BASE_DIR
PI_FILE_SERVER_PORT=8000
# Uncomment and set these for HTTPS
#PI_FILE_SERVER_SSL_CERT=/path/to/cert.pem
#PI_FILE_SERVER_SSL_KEY=/path/to/key.pem
EOL

    # Create test script to verify Python environment
    TEST_SCRIPT="$INSTALL_DIR/test_env.py"
    cat > "$TEST_SCRIPT" << 'EOL'
import sys
import os

print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("PYTHONPATH:", os.environ.get('PYTHONPATH'))
print("Working directory:", os.getcwd())
try:
    import flask
    print("Flask version:", flask.__version__)
except ImportError as e:
    print("Error importing Flask:", e)
EOL

    chown "$ACTUAL_USER:$ACTUAL_USER" "$TEST_SCRIPT"
    chmod 755 "$TEST_SCRIPT"

    # Create startup script in user's home directory
    STARTUP_SCRIPT="$ACTUAL_HOME/.local/bin/start_pifileserver.sh"
    mkdir -p "$(dirname "$STARTUP_SCRIPT")"
    
    cat > "$STARTUP_SCRIPT" << EOL
#!/bin/bash
export XDG_RUNTIME_DIR="/run/user/\$(id -u)"
export PYTHONPATH="$INSTALL_DIR"
export VIRTUAL_ENV="$INSTALL_DIR/venv"
export PATH="$INSTALL_DIR/venv/bin:\$PATH"

echo "Testing Python environment..."
"$INSTALL_DIR/venv/bin/python3" "$INSTALL_DIR/test_env.py"

echo "Starting service..."
systemctl --user daemon-reload
sleep 2
mkdir -p ~/.config/systemd/user/default.target.wants
ln -sf ~/.config/systemd/user/pifileserver.service ~/.config/systemd/user/default.target.wants/pifileserver.service
systemctl --user enable pifileserver
sleep 2
systemctl --user start pifileserver
sleep 2
echo "Service status:"
systemctl --user status pifileserver
echo "Service logs:"
journalctl --user -u pifileserver --no-pager -n 50
EOL

    # Set up systemd service for the user
    echo "Setting up systemd user service..."
    mkdir -p "$ACTUAL_HOME/.config/systemd/user"
    cat > "$SERVICE_FILE" << EOL
[Unit]
Description=Pi File Server
After=network.target

[Service]
Type=simple
Environment="PYTHONPATH=$INSTALL_DIR"
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=$INSTALL_DIR/venv"
Environment="PYTHONUNBUFFERED=1"
Environment="DEBUG=1"
Environment="FLASK_APP=$INSTALL_DIR/app.py"
Environment="FLASK_ENV=development"
EnvironmentFile=$ENV_FILE
WorkingDirectory=$INSTALL_DIR

# Pre-start checks
ExecStartPre=/bin/sh -c 'echo "Starting Pi File Server in \$(pwd)"'
ExecStartPre=/bin/sh -c 'test -f "$INSTALL_DIR/app.py" || (echo "app.py not found in $INSTALL_DIR" && exit 1)'
ExecStartPre=/bin/sh -c 'test -d "$INSTALL_DIR/venv" || (echo "Virtual environment not found in $INSTALL_DIR/venv" && exit 1)'
ExecStartPre=/bin/sh -c '$INSTALL_DIR/venv/bin/python3 -c "import flask; print(\"Flask version:\", flask.__version__)"'

# Run the app through the wrapper script
ExecStart=$INSTALL_DIR/run_app.sh

Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOL

    # Create a wrapper script for the app
    WRAPPER_SCRIPT="$INSTALL_DIR/run_app.sh"
    cat > "$WRAPPER_SCRIPT" << EOL
#!/bin/bash
export PYTHONPATH="$INSTALL_DIR"
export VIRTUAL_ENV="$INSTALL_DIR/venv"
export PATH="$INSTALL_DIR/venv/bin:\$PATH"
export FLASK_APP="$INSTALL_DIR/app.py"
export FLASK_ENV="development"
export DEBUG=1

cd "$INSTALL_DIR"

# Print debug info
echo "Current directory: \$(pwd)"
echo "Python path: \$(which python3)"
echo "Flask path: \$(python3 -c 'import flask; print(flask.__file__)')"

exec "$INSTALL_DIR/venv/bin/python3" -u "$INSTALL_DIR/app.py" 2>&1
EOL

    chmod 755 "$WRAPPER_SCRIPT"
    chown "$ACTUAL_USER:$ACTUAL_USER" "$WRAPPER_SCRIPT"

    # Set correct permissions
    echo "Setting permissions..."
    chown -R "$ACTUAL_USER:$ACTUAL_USER" "$INSTALL_DIR"
    chown -R "$ACTUAL_USER:$ACTUAL_USER" "$BASE_DIR"
    chown -R "$ACTUAL_USER:$ACTUAL_USER" "$CONFIG_DIR"
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$BASE_DIR"
    chmod 644 "$ENV_FILE"
    chmod 644 "$SERVICE_FILE"

    # Create the default.target.wants directory
    mkdir -p "$ACTUAL_HOME/.config/systemd/user/default.target.wants"
    chown -R "$ACTUAL_USER:$ACTUAL_USER" "$ACTUAL_HOME/.config/systemd/user"

    # Enable lingering for the user (allows user services to run without login)
    echo "Enabling user service capabilities..."
    loginctl enable-linger "$ACTUAL_USER"

    # Run the script as the actual user
    sudo -u "$ACTUAL_USER" bash -c "cd '$INSTALL_DIR' && '$STARTUP_SCRIPT'"

    echo "Installation complete!"
    echo "The Pi File Server is now running at http://localhost:8000"
    echo "Files are stored in: $BASE_DIR"
    echo "Application is installed in: $INSTALL_DIR"
    echo "To check the service status: systemctl --user status pifileserver"
    echo "To view logs: journalctl --user -u pifileserver"
    echo "Configuration file: $ENV_FILE"

    # Check if service is actually running
    if ! sudo -u "$ACTUAL_USER" systemctl --user is-active pifileserver >/dev/null 2>&1; then
        echo ""
        echo "WARNING: Service may not have started properly."
        echo "Please check the status with: systemctl --user status pifileserver"
        echo "And view logs with: journalctl --user -u pifileserver"
        echo "You can also try starting it manually with: systemctl --user start pifileserver"
        echo ""
        echo "Debug information:"
        sudo -u "$ACTUAL_USER" bash -c "cd '$INSTALL_DIR' && $INSTALL_DIR/venv/bin/python3 test_env.py"
    fi
}

# Main script
case "${1:-}" in
    uninstall)
        uninstall
        ;;
    *)
        install
        ;;
esac
