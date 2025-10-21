#!/bin/bash
# Script to install, reinstall, or uninstall Fogbed
# Author: Antonio A T R Coutinho (Revised by Gemini)
# Last updated: 2025-10-20
# System version: Ubuntu Server 24.04

FOGBED_DIR="/opt/fogbed"
SERVICE_NAME="fogbed-worker.service"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME"

show_help() {
    echo "Usage: $0 [OPTION]"
    echo "This script manages the Fogbed installation."
    echo ""
    echo "Options:"
    echo "  (no option)            Installs or reinstalls Fogbed."
    echo "  -remove                Remove Fogbed virtual environment and systemd Work service."
    echo "  -systemd-disabled      Installs Fogbed but does not set up the systemd service."
    echo "  -h, --help             Show this help message and exit."
    echo ""
    echo "Description:"
    echo "  Installs Fogbed with all dependencies such as Python, Ansible and Containernet/Mininet."
    echo "  It will replace existing installations in '$FOGBED_DIR' and '$CONTAINERNET_DIR'."
}

create_fogbed_worker_service() {
    local target_path="$1"
    cat > "$target_path" << 'EOF'
[Unit]
Description=fogbed-worker
After=network.target
Requires=docker.service

[Service]
User=root
Group=root
WorkingDirectory=/opt/fogbed
ExecStart=/opt/fogbed/venv/bin/RunWorker
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
IgnoreSIGPIPE=true
Restart=always
RestartSec=3
Type=simple

[Install]
WantedBy=multi-user.target
EOF
}

uninstall() {
    echo "Starting Fogbed Uninstallation ..."

    # Step 1: Stop and remove the systemd service
    echo "[1/3] Checking for systemd service '$SERVICE_NAME' ..."
    if [ -f "$SERVICE_FILE" ]; then
        echo "      Service found. Stopping, disabling, and removing ..."
        sudo systemctl stop "$SERVICE_NAME" || true # Ignore error if not running
        sudo systemctl disable "$SERVICE_NAME"
        sudo rm "$SERVICE_FILE"
        sudo systemctl daemon-reload
        echo "      Service removed successfully."
    else
        echo "      INFO: Service file not found."
    fi

    # Step 2: Remove installation files and directories
    echo "[2/3] Removing installation files and directories ..."
    if [ -d "$FOGBED_DIR" ]; then
        echo "      Removing Fogbed directory '$FOGBED_DIR' ..."
        sudo rm -rf "$FOGBED_DIR"
    else
        echo "      INFO: Fogbed directory not found."
    fi
    if [ -f "/usr/local/bin/fogbed" ]; then
        echo "      Removing system command '/usr/local/bin/fogbed' ..."
        sudo rm /usr/local/bin/fogbed
        echo "      Fogbed system command removed successfully."
    else
        echo "      INFO: '/usr/local/bin/fogbed' file not found."
    fi

    # Step 3: Inform about remaining dependencies
    echo "[3/3] Displaying notice about Fogbed system dependencies:"
    echo "WARNING: This script has removed the Fogbed virtual environment directory and systemd Work service."
    echo "However, it does NOT uninstall system-wide dependencies to avoid breaking other applications."
    echo "The following components may still be installed on your system:"
    echo "   1. System Packages (via APT):"
    echo "     - The original installer added packages like 'git', 'curl', 'ansible', and 'python3-pip'."
    echo "     - If you are certain you no longer need them, you can remove them with:"
    echo "       sudo apt autoremove --purge git curl ansible python3-pip"
    echo "   2. Containernet/Mininet Components:"
    echo "     - The Containernet 'install.sh' script installed Docker, Mininet and Open vSwitch (OVS)."
    echo "     - The correct way to clean up Mininet components is by using Mininet's own uninstaller."
    echo "     - To do this, download the containernet source code directory and run the following script:"
    echo "       git clone https://github.com/containernet/containernet.git"
    echo "       cd containernet/util"
    echo "       sudo ./install.sh -c"
    echo "     - Also, see the official documentation at docker.com on how to uninstall Docker." 
    echo "Fogbed uninstallation finished. Cleaning up the dependencies listed above is optional."
    exit 0
}

install() {
    local install_systemd=$1 # Receives true or false
    
    echo "Starting Fogbed Installation ..."

    echo "[1/5] Installing system dependencies (apt) ..."
    sudo apt-get update
    # Install networks tools for use with fogbed and containers
    sudo apt -y install net-tools iproute2 iputils-ping tcpdump iperf
    sudo apt-get install -y python3 python3-pip git curl ansible
    # Install venv package dynamically based on python version
    sudo apt-get install -y python$(python3 --version | awk '{print $2}' | cut -d '.' -f 1,2)-venv
    
    echo "[2/5] Setting up Fogbed working directory ..."
    if [ -d "$FOGBED_DIR" ]; then 
        echo "      Found existing directory '$FOGBED_DIR'. Removing it for a clean install ..."
        sudo rm -rf "$FOGBED_DIR"
    fi 
    echo "      Creating Fogbed working directory at '$FOGBED_DIR' ..."
    sudo mkdir "$FOGBED_DIR"
    sudo chown root:root "$FOGBED_DIR" 

    echo "[3/5] Installing Containernet ..."
    echo "      Cloning Containernet repository into '$FOGBED_DIR/containernet' ..."
    sudo git clone https://github.com/containernet/containernet.git "$FOGBED_DIR/containernet"
    
    echo "      Running Ansible playbook to install Containernet/Mininet dependencies ..."
    sudo ansible-playbook -i "localhost," -c local "$FOGBED_DIR/containernet/ansible/install.yml"

    echo "[4/5] Setting up Fogbed virtual environment ..."

    echo "      Creating Python virtual environment inside '$FOGBED_DIR' ..."
    sudo python3 -m venv "$FOGBED_DIR/venv"

    echo "      Installing Containernet and Fogbed into the virtual environment ..."
    sudo "$FOGBED_DIR/venv/bin/pip" install "$FOGBED_DIR/containernet"
    sudo "$FOGBED_DIR/venv/bin/pip" install fogbed

    echo "      Setting up Fogbed system commands to virtual environment ..."
    echo "      Creating a symbolic link for /opt/fogbed/venv/bin/fogbed at /usr/local/bin/fogbed ..."
    sudo ln -s /opt/fogbed/venv/bin/fogbed /usr/local/bin/fogbed
    echo "      Creating a symbolic link for /opt/fogbed/venv/bin/mn at /usr/local/bin/mn ..."
    sudo ln -s /opt/fogbed/venv/bin/mn /usr/local/bin/mn

    echo "[5/5] Configuring systemd service ..."
    if [ "$install_systemd" = true ]; then
        echo "      Setting up Fogbed Worker as a systemd service ..."
        create_fogbed_worker_service "/tmp/$SERVICE_NAME"
        sudo mv "/tmp/$SERVICE_NAME" "$SERVICE_FILE"
        sudo sed -i "s#/opt/fogbed#$FOGBED_DIR#g" "$SERVICE_FILE"
        sudo systemctl enable "$SERVICE_NAME"
        sudo systemctl restart "$SERVICE_NAME"
        echo "      Service enabled and started. Verifying status:"
        sudo systemctl status --no-pager "$SERVICE_NAME"
    else
        echo "      INFO: Skipping systemd service setup as requested by '-systemd-disabled' flag."
    fi

    echo ""
    echo "Installation Finished."
    exit 0
}

# Must be run as root/sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo." 
   exit 1
fi

# Parameter Parsing
case "$1" in
    -h|--help)
        show_help
        ;;
    -remove)
        uninstall
        ;;
    -systemd-disabled)
        install false
        ;;
    ""|*) # Default case for installation, including unknown params
        if [ -n "$1" ]; then
            echo "ERROR: Unknown option '$1'."
            show_help
            exit 1
        fi
        install true
        ;;
esac

