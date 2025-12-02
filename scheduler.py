#!/usr/bin/env python3
"""
Tasmota Smart Plug Scheduler with Dynamic Sunset Calculation
Turns plugs ON at sunset and OFF at a specified time
"""

import subprocess
import os
from datetime import datetime, timedelta
from astral.sun import sun

# Import configuration
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PLUGS, TIMEZONE, LOCATION, OFF_TIME, LOG_FILE

def log(message, always=False):
    """Log message - only logs actions by default to reduce SD card writes"""
    timestamp = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    
    if always or "✓" in message or "✗" in message or "Executing" in message:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(log_msg + "\n")

def control_plug(ip, action):
    """Send command to Tasmota plug"""
    cmd = "Power%20On" if action == "on" else "Power%20Off"
    try:
        result = subprocess.run(
            ['curl', '-s', f'http://{ip}/cm?cmnd={cmd}'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return "SUCCESS" in result.stdout or "ON" in result.stdout or "OFF" in result.stdout
    except Exception as e:
        log(f"Error controlling plug {ip}: {e}", always=True)
        return False

def get_sunset_time():
    """Calculate today's sunset time"""
    now = datetime.now(TIMEZONE)
    s = sun(LOCATION.observer, date=now.date(), tzinfo=TIMEZONE)
    return s['sunset']

def get_next_run_time():
    """Calculate next scheduled run time"""
    now = datetime.now(TIMEZONE)
    sunset_today = get_sunset_time()
    
    off_hour, off_min = map(int, OFF_TIME.split(':'))
    off_today = now.replace(hour=off_hour, minute=off_min, second=0, microsecond=0)
    
    if now < sunset_today:
        return sunset_today, "on"
    elif now < off_today:
        return off_today, "off"
    else:
        tomorrow = now.date() + timedelta(days=1)
        s = sun(LOCATION.observer, date=tomorrow, tzinfo=TIMEZONE)
        return s['sunset'], "on"

def main():
    next_time, next_action = get_next_run_time()
    now = datetime.now(TIMEZONE)
    
    time_diff = abs((next_time - now).total_seconds())
    
    if time_diff < 120:  # Within 2 minutes
        log(f"Executing scheduled action: {next_action.upper()}", always=True)
        for plug in PLUGS:
            success = control_plug(plug['ip'], next_action)
            if success:
                log(f"✓ {plug['name']} turned {next_action.upper()}")
            else:
                log(f"✗ Failed to control {plug['name']}")

if __name__ == "__main__":
    main()
