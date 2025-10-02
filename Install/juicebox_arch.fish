#!/usr/bin/env fish
# Script de instalación del servicio systemd para JuiceBox Engine en Arch con shell Fish

set -e

# Detecta la ruta absoluta de la carpeta raíz de la app (JuiceBox)
set script_dir (dirname (status -f))
set app_dir (realpath "$script_dir/..")

echo ">=== Creating juicebox user and directories ===<"
if not id -u juicebox >/dev/null 2>&1
    sudo useradd -r -s /usr/bin/nologin -U juicebox
end
sudo mkdir -p /opt/juicebox
sudo chown -R juicebox:juicebox /opt/juicebox
sudo usermod -aG docker juicebox

echo "=== Copying JuiceBox app from $app_dir to /opt/juicebox ==="
sudo rsync -av --exclude venv "$app_dir/" /opt/juicebox/
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

echo ">=== Creating systemd service unit ===<"
echo "[Unit]
Description=JuiceBox CTF Orchestrator for Root The Box & OWASP Juice Shop
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=juicebox
Group=juicebox
WorkingDirectory=/opt/juicebox
ExecStart=/opt/juicebox/venv/bin/juicebox
Environment=JUICEBOX_SOCKET=/opt/juicebox/run/engine.sock
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target" \
| sudo tee /etc/systemd/system/juiceboxengine.service > /dev/null

echo "=== Reloading systemd daemon ==="
sudo systemctl daemon-reload

echo "=== Enabling and starting service ==="
sudo systemctl enable --now juiceboxengine.service

echo "=== Checking service status ==="
systemctl status juiceboxengine.service --no-pager

echo "<=== JuiceBox Engine installation completed ===>"
