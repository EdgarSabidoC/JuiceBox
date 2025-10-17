#!/usr/bin/env bash
# Script de desinstalación del servicio systemd para JuiceBox Engine + WebClient en Ubuntu/Debian con shell Bash

set -euo pipefail

echo ">=== Stopping Juice Box Engine ===<"
sudo systemctl stop juiceboxengine.service || true
sudo systemctl disable juiceboxengine.service || true

echo ">=== Stopping Juice Box WebClient ===<"
sudo systemctl stop juiceboxweb.service || true
sudo systemctl disable juiceboxweb.service || true

echo "=== Removing systemd files ==="
sudo rm -f /etc/systemd/system/juiceboxengine.service
sudo rm -f /etc/systemd/system/juiceboxweb.service
sudo systemctl daemon-reload

echo "=== Removing app and virtual environment ==="
sudo rm -rf /opt/juicebox

echo "=== Removing TUI wrapper ==="
sudo rm -f /usr/local/bin/juicebox-tui

echo "=== Removing user and juicebox group ==="
if id juicebox >/dev/null 2>&1; then
    # userdel -r elimina el home si existe, deluser es más común en Debian/Ubuntu
    sudo userdel -r juicebox || sudo deluser --remove-home juicebox || true
fi
if getent group juicebox >/dev/null 2>&1; then
    sudo groupdel juicebox || true
fi

echo "=== Cleaning journald logs ==="
# Solo rota y limpia entradas de JuiceBox, sin borrar todos los logs del sistema
sudo journalctl -u juiceboxengine.service --rotate || true
sudo journalctl -u juiceboxengine.service --vacuum-time=1s || true
sudo journalctl -u juiceboxweb.service --rotate || true
sudo journalctl -u juiceboxweb.service --vacuum-time=1s || true

echo "<=== Juice Box uninstallation completed ===>"
