#!/usr/bin/env bash

# Script de desinstalación del servicio systemd para JuiceBox Engine en Ubuntu/Debian

set -e

echo ">=== Stopping Juice Box Engine ===<"
sudo systemctl stop juiceboxengine.service || true
sudo systemctl stop juiceboxengine.socket || true
sudo systemctl disable juiceboxengine.service || true
sudo systemctl disable juiceboxengine.socket || true
sudo systemctl daemon-reload

echo "=== Removing systemd files ==="
sudo rm -f /etc/systemd/system/juiceboxengine.service
sudo rm -f /etc/systemd/system/juiceboxengine.socket
sudo systemctl daemon-reload

echo "=== Removing app and virtual environment ==="
sudo rm -rf /opt/juicebox

echo "=== Removing user and juicebox group ==="
if id "juicebox" &>/dev/null; then
    sudo deluser --remove-home juicebox || sudo userdel -r juicebox
fi
if getent group juicebox &>/dev/null; then
    sudo groupdel juicebox
fi


echo "=== Cleaning journald logs ==="
echo "Rotando y eliminando logs de juiceboxengine..."
sudo journalctl SYSLOG_IDENTIFIER=juiceboxengine --rotate
sudo journalctl --vacuum-time=1s

echo "<=== Juice Box uninstallation completed ===>"
