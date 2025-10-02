#!/usr/bin/env bash
# Script de instalación del servicio systemd para JuiceBox Engine en Ubuntu/Debian con shell Bash

set -e


# Detecta la ruta absoluta de la carpeta raíz de la app (JuiceBox)
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo ">=== Creating juicebox user and directories ===<"
sudo adduser --system --group juicebox || true
sudo mkdir -p /opt/juicebox
sudo chown -R juicebox:juicebox /opt/juicebox
sudo usermod -aG docker juicebox
newgrp docker

echo "=== Copying JuiceBox app from $APP_DIR to /opt/juicebox ==="
sudo rsync -av --exclude venv "$APP_DIR/" /opt/juicebox/
sudo chown -R juicebox:juicebox /opt/juicebox

echo "=== Creating Python virtual environment ==="
cd /opt/juicebox
sudo -u juicebox python3 -m venv /opt/juicebox/venv
sudo -u juicebox /opt/juicebox/venv/bin/python -m ensurepip --upgrade
sudo -u juicebox /opt/juicebox/venv/bin/python -m pip install --upgrade pip

echo "=== Installing dependencies from requirements.txt ==="
sudo -u juicebox /opt/juicebox/venv/bin/pip install -r /opt/juicebox/requirements.txt

echo "=== Installing JuiceBox package in editable mode ==="
sudo -u juicebox /opt/juicebox/venv/bin/pip install -e /opt/juicebox

echo ">=== Creating systemd socket unit ===<"
sudo tee /etc/systemd/system/juiceboxengine.socket > /dev/null <<'EOF'
[Unit]
Description=Socket for JuiceBox Engine
PartOf=juiceboxengine.service

[Socket]
ListenStream=/run/juicebox/engine.sock
SocketMode=0660
SocketUser=juicebox
SocketGroup=docker
RuntimeDirectory=juicebox
RuntimeDirectoryMode=0755

[Install]
WantedBy=sockets.target
EOF

echo ">=== Creating systemd service unit ===<"
sudo tee /etc/systemd/system/juiceboxengine.service > /dev/null <<'EOF'
[Unit]
Description=JuiceBox CTF Orchestrator for Root The Box & OWASP Juice Shop
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=juicebox
Group=juicebox
WorkingDirectory=/opt/juicebox
ExecStart=/opt/juicebox/venv/bin/python -m JuiceBox
Environment="JUICEBOX_SOCKET=/run/juicebox/engine.sock"
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "=== Reloading systemd daemon ==="
sudo systemctl daemon-reload

echo "=== Enabling socket and service ==="
sudo systemctl enable juiceboxengine.socket
sudo systemctl enable juiceboxengine.service

echo "=== Starting socket ==="
sudo systemctl start juiceboxengine.socket

echo "=== Checking service and socket status ==="
systemctl status juiceboxengine.socket --no-pager
systemctl status juiceboxengine.service --no-pager

echo "<=== JuiceBox Engine installation completed ===>"
