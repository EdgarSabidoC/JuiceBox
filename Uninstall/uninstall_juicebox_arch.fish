#!/usr/bin/env fish
set -e

echo ">=== Stopping Juice Box Engine ===<"
sudo systemctl stop juiceboxengine.service; or true
sudo systemctl stop juiceboxengine.socket; or true
sudo systemctl disable juiceboxengine.service; or true
sudo systemctl disable juiceboxengine.socket; or true
sudo systemctl daemon-reload

echo "=== Removing systemd files ==="
sudo rm -f /etc/systemd/system/juiceboxengine.service
sudo rm -f /etc/systemd/system/juiceboxengine.socket
sudo systemctl daemon-reload

echo "=== Removing app and virtual environment ==="
sudo rm -rf /opt/juicebox

echo "=== Removing user and juicebox group ==="
if id juicebox > /dev/null 2>&1
    sudo userdel -r juicebox; or sudo deluser --remove-home juicebox
end
if getent group juicebox > /dev/null 2>&1
    sudo groupdel juicebox
end

echo "=== Cleaning journald logs ==="
sudo journalctl SYSLOG_IDENTIFIER=juiceboxengine --rotate
sudo journalctl --vacuum-time=1s

echo "<=== Juice Box uninstallation completed ===>"
