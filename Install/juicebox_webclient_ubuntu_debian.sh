#!/usr/bin/env bash
# Script de instalación del servicio systemd para JuiceBox WebClient en Debian/Ubuntu

set -e

echo ">=== Creating systemd service for JuiceBox WebClient ===<"
SERVICE_FILE="/etc/systemd/system/juiceboxweb.service"

sudo tee $SERVICE_FILE > /dev/null <<'EOF'
[Unit]
Description=JuiceBox WebClient API (FastAPI)
After=network.target juiceboxengine.service
Requires=juiceboxengine.service

[Service]
Type=simple
User=juicebox
Group=juicebox
WorkingDirectory=/opt/juicebox
EnvironmentFile=/opt/juicebox/WebClient/.env
ExecStart=/opt/juicebox/venv/bin/gunicorn -k uvicorn.workers.UvicornWorker WebClient.main:app -b ${HOST}:${PORT} --workers 4
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "=== Reloading systemd daemon ==="
sudo systemctl daemon-reload

echo "=== Enabling juiceboxweb service ==="
sudo systemctl enable juiceboxweb

echo "=== Starting juiceboxweb service ==="
sudo systemctl start juiceboxweb

echo "=== Checking service status ==="
sudo systemctl status juiceboxweb --no-pager

echo "<=== JuiceBox WebClient installation completed ===>"

