#!/bin/bash
set -e

echo "Installing Smart Home Control..."

# Install dependencies
pip3 install flask astral pytz --break-system-packages

# Create log directory
mkdir -p /var/log/smart-home

# Install systemd service
cp smart-home.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable smart-home
systemctl start smart-home

# Setup cron for scheduler
(crontab -l 2>/dev/null | grep -v scheduler.py; echo "* * * * * cd /root/smart-home && /usr/bin/python3 /root/smart-home/scheduler.py >> /var/log/smart-home/scheduler.log 2>&1") | crontab -

echo "Installation complete!"
echo "Web interface running on port 5000"
systemctl status smart-home --no-pager
