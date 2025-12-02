"""Configuration for Smart Home Control"""
import pytz
from astral import LocationInfo

# Location settings for sunset calculation
TIMEZONE = pytz.timezone('America/Los_Angeles')
LOCATION = LocationInfo("Portland", "USA", "America/Los_Angeles", 45.5152, -122.6784)

# Plug configuration
PLUGS = [
    {"name": "Evening Lamp", "ip": "10.0.0.13", "id": "plug1"}
]

# Schedule settings
OFF_TIME = "23:00"  # 11 PM

# Paths
LOG_FILE = "/var/log/smart-home/scheduler.log"
