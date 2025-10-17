#!/usr/bin/env fish
# Script de desinstalación del servicio systemd para JuiceBox Engine + WebClient en Arch con shell Fish

set -e

echo ">=== Stopping Juice Box Engine ===<"
sudo systemctl stop juiceboxengine.service; or true
sudo systemctl disable juiceboxengine.service; or true

echo ">=== Stopping Juice Box WebClient ===<"
sudo systemctl stop juiceboxweb.service; or true
sudo systemctl disable juiceboxweb.service; or true

echo "=== Removing systemd files ==="
sudo rm -f /etc/systemd/system/juiceboxengine.service
sudo rm -f /etc/systemd/system/juiceboxweb.service
sudo systemctl daemon-reload

echo "=== Removing app and virtual environment ==="
sudo rm -rf /opt/juicebox

echo "=== Removing TUI wrapper ==="
sudo rm -f /usr/local/bin/juicebox-tui

echo "=== Removing user and juicebox group ==="
if id juicebox > /dev/null 2>&1
    sudo userdel -r juicebox; or sudo deluser --remove-home juicebox
end
if getent group juicebox > /dev/null 2>&1
    sudo groupdel juicebox
end

echo "=== Cleaning journald logs ==="
# Solo rota y limpia entradas de JuiceBox, sin borrar todos los logs del sistema
sudo journalctl -u juiceboxengine.service --rotate
sudo journalctl -u juiceboxengine.service --vacuum-time=1s
sudo journalctl -u juiceboxweb.service --rotate
sudo journalctl -u juiceboxweb.service --vacuum-time=1s

echo "<=== Juice Box uninstallation completed ===>"
