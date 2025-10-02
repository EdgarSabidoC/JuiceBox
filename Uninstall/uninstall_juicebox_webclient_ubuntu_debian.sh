#!/usr/bin/env bash

# Script de desinstalación del servicio systemd para JuiceBox WebClient en Ubuntu/Debian

set -e

echo ">=== Stopping JuiceBox WebClient ===<"
sudo systemctl stop juiceboxweb.service || true
sudo systemctl disable juiceboxweb.service || true
sudo systemctl daemon-reload

echo "=== Removing systemd service file ==="
sudo rm -f /etc/systemd/system/juiceboxweb.service
sudo systemctl daemon-reload

echo "=== Cleaning journald logs for juiceboxweb ==="
sudo journalctl -u juiceboxweb --rotate
sudo journalctl -u juiceboxweb --vacuum-time=1s

echo "<=== JuiceBox WebClient uninstallation completed ===>"
