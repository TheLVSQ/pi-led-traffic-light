# 🟢 Raspberry Pi Status & Traffic Light Dashboard

A lightweight Flask-based web dashboard for the **Raspberry Pi Zero 2 W** that displays system status, controls LED segments, manages Wi-Fi connections, and runs a fully automated **traffic-light-style scheduler**.  
Designed for easy deployment in environments like coffee shops or offices where the Pi operates independently.

---

## ✨ Features

- **Web Dashboard** — View system info: IP, CPU temp, Wi-Fi signal, and uptime.
- **LED Traffic Light Scheduler**  
  - Three configurable segments (Green, Yellow, Red).  
  - Define custom LED counts, colors, and start/end indexes.  
  - Automatic hourly schedule:
    | Time | Action |
    |------|--------|
    | `:59` | Yellow segment on |
    | `:00` | Red segment on |
    | `:01` | Green segment on |
- **Wi-Fi Configuration Page** — Add or update network SSIDs and passwords directly from the web interface.
- **Auto-Fallback Access Point** — If Wi-Fi fails, the Pi creates its own hotspot (`RRPi-Setup`) so you can connect at `http://192.168.50.1:8080/wifi` and reconfigure.
- **Secure Login Page** — Protects all routes with a session-based login.
- **Systemd Service** — Runs automatically on boot.
- **Visual Feedback** — LED strip briefly flashes when configuration changes are applied.
- **Live Clock** — Displays current local time and upcoming schedule triggers.

---

## 🧩 Hardware Requirements

- **Raspberry Pi Zero 2 W** (or any Pi with GPIO and Wi-Fi)
- **WS2812B / NeoPixel LED strip**
  - Data line → GPIO18 (pin 12)
  - 5 V power supply shared with Pi ground

---

## ⚙️ Software Requirements

- Raspberry Pi OS (Bookworm or newer)
- Python 3.11 +
- Flask, Flask-Login, APScheduler, rpi-ws281x, psutil, netifaces

Install prerequisites:
```bash
sudo apt update
sudo apt install python3-venv python3-pip hostapd dnsmasq tzdata -y
```

## 🚀 Installation

```bash
git clone https://github.com/<yourusername>/pi-status-dashboard.git
cd pi-status-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

Copy the example config files:

```bash
cp config.example.json config.json
cp statuspage.service.example /etc/systemd/system/statuspage.service
```
Enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable statuspage.service
sudo systemctl start statuspage.service
```
Then visit your Pi:
```
http://<pi_ip>:8080/login
```

