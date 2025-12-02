# Smart Home Control

A lightweight Flask-based web interface for controlling Tasmota smart plugs with automated sunset/bedtime scheduling.

## Features

- 🏠 Web dashboard with dark/light mode
- 🌅 Automatic sunset-based scheduling using astral library
- ⏰ Configurable off-time scheduling
- 🔌 Toggle/On/Off controls for Tasmota devices
- 📍 Location-aware sunset calculation (defaults to Portland, OR)

## Installation

1. Clone this repo:
   ```bash
   git clone https://github.com/yourusername/smart-home.git
   cd smart-home
   ```

2. Run the install script (requires root):
   ```bash
   sudo ./install.sh
   ```

## Configuration

Edit `config.py` to customize:

- **PLUGS**: Add/modify your Tasmota device IPs and names
- **LOCATION**: Set your coordinates for sunset calculation
- **OFF_TIME**: Set when lights should turn off (24h format)

## Manual Usage

Start the web server:
```bash
python3 web.py
```

Run the scheduler manually:
```bash
python3 scheduler.py
```

## Files

- `config.py` - Configuration settings
- `web.py` - Flask web interface
- `scheduler.py` - Sunset/off-time automation (runs via cron)
- `smart-home.service` - systemd service file
- `install.sh` - Installation script

## Dependencies

- Python 3.x
- Flask
- astral
- pytz

## License

MIT
