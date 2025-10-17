# Raspberry Pi Status & Traffic Light Dashboard

A lightweight Flask-based web dashboard for the Raspberry Pi that displays system status, manages Wi‑Fi, and drives a WS2812/NeoPixel LED strip as a three‑segment “traffic light,” with an hourly scheduler.

Works well for standalone deployments (e.g., coffee shops, offices) where the Pi runs headless and shows status at a glance.

---

## Features

- Web dashboard: IP, CPU temp/usage, memory, disk, Wi‑Fi SSID/signal, uptime.
- LED traffic‑light scheduler:
  - Three configurable segments (green, yellow, red).
  - Custom LED counts, colors, and start/end indexes per segment.
  - Hourly triggers (e.g., Yellow at :59, Red at :00, Green at :01).
- Wi‑Fi page: Append SSID/PSK to `wpa_supplicant.conf` and reconnect.
- Secure login: Session‐based authentication using a `users.json` password hash file.
- Systemd service: Boot‑time startup with automatic restart.
- Visual feedback: Brief LED flash after saving new configuration.
- Live clock: Local time and upcoming scheduler minutes on the dashboard.

---

## Hardware Requirements

- Raspberry Pi Zero 2 W (or any Pi with GPIO + Wi‑Fi)
- WS2812B / NeoPixel LED strip
  - Data line: GPIO18 (pin 12)
  - Power: 5V with common ground to the Pi

---

## Software Requirements

- Raspberry Pi OS (Bookworm or newer)
- Python 3.11+
- System packages: `python3-venv` `python3-pip` `tzdata`
  - For Wi‑Fi page to apply changes: `wpa_cli` and `dhcpcd` (usually present on Raspberry Pi OS)

Install prerequisites (on the Pi):
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip tzdata
```

---

## Quick Start (Development)

1) Clone and install dependencies:
```bash
git clone <this repo>
cd pi-led-traffic-light
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2) Create required files:
```bash
cp config.example.json config.json
cp users.example.json users.json
# Replace the placeholder hash in users.json (see “Users & Auth” below)
```

3) Run the app:
```bash
FLASK_SECRET='changeme' python app.py
# App listens on http://0.0.0.0:8080
```

4) Open the UI:
```
http://<pi_ip_or_hostname>:8080/login
```

---

## Users & Auth

The app uses `users.json` in the working directory to validate logins. File format:
```json
{
  "admin": "<werkzeug_password_hash>"
}
```

Generate a password hash (choose one):
- Using the helper script:
  ```bash
  source venv/bin/activate
  python scripts/create_user.py --file users.json --username admin --password '<your_password>'
  ```
- Or via Python one‑liner:
  ```bash
  python - <<'PY'
  from werkzeug.security import generate_password_hash
  print(generate_password_hash('<your_password>'))
  PY
  # Paste the output hash into users.json
  ```

Environment variable `FLASK_SECRET` should be set in production.

---

## LED Configuration

LED settings are stored in `config.json`. Example fields (see `config.example.json`):
- `led_count`: total LEDs in the strip
- `segments`: start/end indexes for `red`, `yellow`, `green`
- `colors`: RGB arrays per segment
- `schedule`: minutes past each hour to activate yellow/red/green
- `scheduler_enabled`: enable/disable hourly jobs

Important: The LED control module uses an absolute path by default:
```
/home/rrpi/statuspage/config.json
```
Ensure your deployment places `config.json` at that path, or update `CONFIG_PATH` in `led_control.py` to match your environment.

On save (via the /config page), the strip briefly flashes for visual confirmation and the scheduler is reloaded.

---

## Routes

- `/login` – Session login using `users.json`
- `/` – Status dashboard (system and Wi‑Fi info, schedule preview)
- `/config` – Configure LED count/segments/colors and scheduler minutes
- `/wifi` – Append SSID/PSK to wpa_supplicant and reconnect

`/config` and `/wifi` require login.

---

## Systemd Deployment (Recommended)

1) Copy the service file and adjust paths/users as needed:
```bash
sudo cp statuspage.service.example /etc/systemd/system/statuspage.service
sudo systemctl daemon-reload
```

2) Create the app directory and files (matching the service WorkingDirectory):
```bash
sudo mkdir -p /home/rrpi/statuspage
sudo chown -R rrpi:rrpi /home/rrpi/statuspage
# Place repo contents there; create/activate venv; install requirements; add users.json and config.json
```

3) Start and enable on boot:
```bash
sudo systemctl enable --now statuspage.service
sudo systemctl status statuspage.service
```

Then browse to `http://<pi_ip>:8080/login`.

Note: `/wifi` writes `/etc/wpa_supplicant/wpa_supplicant.conf` and runs `wpa_cli` + restarts `dhcpcd`. The service user needs permission to perform these actions (passwordless sudo or run as root). Adjust your security model accordingly.

---

## Hardware Notes

- Data pin: GPIO18 (pin 12) is used by the WS2812 driver in `rpi_ws281x`.
- Provide sufficient 5V power for the strip; connect grounds together.
- Avoid drawing high current from the Pi’s 5V rail; power the strip separately when needed.

---

## Troubleshooting

- LEDs do not light:
  - Confirm `config.json` path matches `led_control.py`’s `CONFIG_PATH`.
  - Verify correct data pin (GPIO18) and adequate power.
  - Ensure the service user can access `/dev/mem` if using DMA (typical for `rpi_ws281x`).
- Scheduler not triggering:
  - Check service logs; APScheduler uses timezone `America/New_York`.
  - Ensure `scheduler_enabled` is true and minutes are valid (0–59).
- Wi‑Fi changes not applied:
  - Verify `wpa_supplicant.conf` was appended and that `wpa_cli`/`dhcpcd` restarted.
  - The service user may require sudo privileges for those operations.
- CPU temp is 0 or N/A:
  - `psutil.sensors_temperatures()` and `vcgencmd` may require firmware support.

---

## Development

- Install deps: `pip install -r requirements.txt`
- Run: `FLASK_SECRET='devsecret' python app.py`
- Code entry point: `app.py`
- LED driver module: `led_control.py`
- System info helpers: `utils.py`

---

## License

See `LICENSE`.

