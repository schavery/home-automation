#!/usr/bin/env python3
"""Flask web interface for Tasmota Smart Plug Control"""
from flask import Flask, render_template_string, jsonify, request
import subprocess
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import PLUGS, TIMEZONE, LOCATION, OFF_TIME
from astral.sun import sun
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Smart Home Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg-primary: #f0f0f0;
            --bg-secondary: #ffffff;
            --bg-schedule: #e3f2fd;
            --text-primary: #000000;
            --text-secondary: #333333;
            --shadow: rgba(0,0,0,0.1);
            --border: #ddd;
        }
        [data-theme="dark"] {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-schedule: #1e3a5f;
            --text-primary: #ffffff;
            --text-secondary: #e0e0e0;
            --shadow: rgba(0,0,0,0.3);
            --border: #444;
        }
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: var(--bg-primary);
            color: var(--text-primary);
            transition: background-color 0.3s, color 0.3s;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .theme-toggle {
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 20px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 20px;
        }
        .plug-card {
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px var(--shadow);
        }
        .plug-name { font-size: 24px; font-weight: bold; margin-bottom: 10px; }
        .status { font-size: 18px; margin: 15px 0; padding: 10px; border-radius: 5px; }
        .status.on { background: #4CAF50; color: white; }
        .status.off { background: #f44336; color: white; }
        button { font-size: 16px; padding: 15px 30px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
        .btn-on { background: #4CAF50; color: white; }
        .btn-off { background: #f44336; color: white; }
        .btn-toggle { background: #2196F3; color: white; }
        .schedule { margin-top: 20px; padding: 15px; background: var(--bg-schedule); border-radius: 5px; }
        .schedule-time { font-weight: bold; color: #1976D2; }
        [data-theme="dark"] .schedule-time { color: #64B5F6; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Smart Home Control</h1>
        <button class="theme-toggle" onclick="toggleTheme()"><span id="theme-icon">🌙</span></button>
    </div>
    {% for plug in plugs %}
    <div class="plug-card">
        <div class="plug-name">{{ plug.name }}</div>
        <div class="status" id="status-{{ plug.id }}">Loading...</div>
        <div>
            <button class="btn-toggle" onclick="togglePlug('{{ plug.ip }}', '{{ plug.id }}')">Toggle</button>
            <button class="btn-on" onclick="controlPlug('{{ plug.ip }}', 'on', '{{ plug.id }}')">Turn ON</button>
            <button class="btn-off" onclick="controlPlug('{{ plug.ip }}', 'off', '{{ plug.id }}')">Turn OFF</button>
        </div>
        <div class="schedule">
            <strong>🌅 Automation Schedule:</strong><br>
            <span id="schedule-info-{{ plug.id }}">Loading schedule...</span>
        </div>
    </div>
    {% endfor %}
    <script>
        function getSystemTheme() { return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'; }
        function applyTheme(theme) {
            document.body.setAttribute('data-theme', theme);
            document.getElementById('theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
        }
        function toggleTheme() {
            const newTheme = document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        }
        function loadTheme() { applyTheme(localStorage.getItem('theme') || getSystemTheme()); }
        function updateStatus(plugId) {
            fetch('/status/' + plugId).then(r => r.json()).then(data => {
                const el = document.getElementById('status-' + plugId);
                el.textContent = 'Status: ' + data.power;
                el.className = 'status ' + data.power.toLowerCase();
            });
        }
        function updateSchedule(plugId) {
            fetch('/schedule').then(r => r.json()).then(data => {
                document.getElementById('schedule-info-' + plugId).innerHTML = 
                    'Turn <span class="schedule-time">ON</span> at sunset (' + data.sunset + ')<br>' +
                    'Turn <span class="schedule-time">OFF</span> at ' + data.off_time;
            });
        }
        function controlPlug(ip, action, plugId) {
            fetch('/control', { method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ip, action}) }).then(() => updateStatus(plugId));
        }
        function togglePlug(ip, plugId) {
            fetch('/toggle', { method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ip}) }).then(() => updateStatus(plugId));
        }
        loadTheme();
        {% for plug in plugs %}
        updateStatus('{{ plug.id }}'); updateSchedule('{{ plug.id }}');
        setInterval(() => updateStatus('{{ plug.id }}'), 5000);
        {% endfor %}
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, plugs=PLUGS)

@app.route('/status/<plug_id>')
def status(plug_id):
    plug = next((p for p in PLUGS if p['id'] == plug_id), None)
    if not plug:
        return jsonify({'error': 'Plug not found'}), 404
    result = subprocess.run(['curl', '-s', f'http://{plug["ip"]}/cm?cmnd=Power'], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        return jsonify({'power': data.get('POWER', 'UNKNOWN')})
    except:
        return jsonify({'power': 'ERROR'})

@app.route('/schedule')
def schedule():
    now = datetime.now(TIMEZONE)
    s = sun(LOCATION.observer, date=now.date(), tzinfo=TIMEZONE)
    return jsonify({
        "sunset": s['sunset'].strftime("%I:%M %p"),
        "off_time": "11:00 PM"
    })

@app.route('/control', methods=['POST'])
def control():
    data = request.json
    cmd = 'Power%20On' if data.get('action') == 'on' else 'Power%20Off'
    subprocess.run(['curl', '-s', f'http://{data.get("ip")}/cm?cmnd={cmd}'])
    return jsonify({'success': True})

@app.route('/toggle', methods=['POST'])
def toggle():
    subprocess.run(['curl', '-s', f'http://{request.json.get("ip")}/cm?cmnd=Power%20TOGGLE'])
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
