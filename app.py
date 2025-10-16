from flask import Flask, render_template, request, render_template_string
import os, socket, time, psutil, subprocess, netifaces, threading, json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from utils import get_system_info, get_wifi_info, reconnect_wifi, clamp_int
from led_control import set_only, turn_all_off, get_config, save_config
from pytz import timezone   # or from zoneinfo import ZoneInfo on Py ≥ 3.9
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from functools import wraps

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "changeme")  # replace in .env later
WPA_SUPPLICANT_FILE = "/etc/wpa_supplicant/wpa_supplicant.conf"

scheduler = BackgroundScheduler(timezone=timezone("America/New_York"))
scheduler_started = False
jobs = []

#-----------------------------------------
# Helper to check credentials
#-----------------------------------------

def verify_user(username, password):
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
        if username in users and check_password_hash(users[username], password):
            return True
    except Exception as e:
        print("Auth error:", e)
    return False


# ─────────────────────────────────────────────
# Wi-Fi helper thread (optional, as you had)
# ─────────────────────────────────────────────
def wifi_monitor():
    while True:
        wifi = get_wifi_info()
        if wifi["ssid"] == "Not connected":
            print("Wi-Fi disconnected – attempting reconnect...")
            reconnect_wifi()
        time.sleep(60)

# ─────────────────────────────────────────────
# Scheduler wiring
# ─────────────────────────────────────────────
def _clear_jobs():
    global jobs
    for j in jobs:
        try:
            scheduler.remove_job(j.id)
        except Exception:
            pass
    jobs = []

def schedule_from_config():
    """(Re)create three hourly jobs from the config (yellow/red/green)."""
    cfg = get_config()
    if not cfg.get("scheduler_enabled", True):
        _clear_jobs()
        return

    y = clamp_int(cfg["schedule"]["yellow_minute"], 0, 59)
    r = clamp_int(cfg["schedule"]["red_minute"],    0, 59)
    g = clamp_int(cfg["schedule"]["green_minute"],  0, 59)

    # Clear old jobs
    _clear_jobs()

    # Define the three “set_only” steps
    def set_yellow():
        print("[Scheduler] YELLOW")
        set_only("yellow")

    def set_red():
        print("[Scheduler] RED")
        set_only("red")

    def set_green():
        print("[Scheduler] GREEN")
        set_only("green")

    # Add cron jobs (every hour at minute y/r/g)
    jobs.append(scheduler.add_job(set_yellow, CronTrigger(minute=y)))
    jobs.append(scheduler.add_job(set_red,    CronTrigger(minute=r)))
    jobs.append(scheduler.add_job(set_green,  CronTrigger(minute=g)))

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    info = get_system_info()
    try:
        cfg = get_config()
    except Exception:
        cfg = {}

    # make safe defaults
    sched = cfg.get("schedule", {"yellow_minute": 59, "red_minute": 0, "green_minute": 1})
    next_events = {
        "yellow": sched.get("yellow_minute", 59),
        "red": sched.get("red_minute", 0),
        "green": sched.get("green_minute", 1),
    }

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    return render_template(
        "index.html",
        info=info,
        cfg=cfg,
        current_time=current_time,
        next_events=next_events,
    )

@app.route("/wifi", methods=["GET", "POST"])
@login_required
def wifi_config():
    message = ""
    current = get_wifi_info()["ssid"]
    if request.method == "POST":
        ssid = request.form.get("ssid")
        psk  = request.form.get("psk")
        if ssid and psk:
            new_entry = f'\nnetwork={{\n    ssid="{ssid}"\n    psk="{psk}"\n}}\n'
            try:
                with open(WPA_SUPPLICANT_FILE, "a") as f:
                    f.write(new_entry)
                reconnect_wifi()
                message = "Network saved successfully."
                return render_template("reboot.html", message=message, ssid=ssid)
            except Exception as e:
                message = f"❌ Failed: {e}"
        else:
            message = "⚠️ SSID and password are required."
    return render_template("wifi.html", current=current, message=message)

@app.route("/config", methods=["GET", "POST"])
@login_required
def config_page():
    cfg = get_config()
    message = ""
    if request.method == "POST":
        try:
            # LED count
            led_count = clamp_int(request.form["led_count"], 1, 4096)

            # Segments
            r0 = clamp_int(request.form["red_start"],    0, led_count-1)
            r1 = clamp_int(request.form["red_end"],      0, led_count-1)
            y0 = clamp_int(request.form["yellow_start"], 0, led_count-1)
            y1 = clamp_int(request.form["yellow_end"],   0, led_count-1)
            g0 = clamp_int(request.form["green_start"],  0, led_count-1)
            g1 = clamp_int(request.form["green_end"],    0, led_count-1)

            # Colors (from hex like #FFB400)
            def hex_to_rgb(h):
                h = h.lstrip("#")
                return [int(h[i:i+2], 16) for i in (0, 2, 4)]

            red_hex    = request.form["red_color"]
            yellow_hex = request.form["yellow_color"]
            green_hex  = request.form["green_color"]

            # Schedule minutes
            y_min = clamp_int(request.form["yellow_minute"], 0, 59)
            r_min = clamp_int(request.form["red_minute"],    0, 59)
            g_min = clamp_int(request.form["green_minute"],  0, 59)

            new_cfg = {
                "led_count": led_count,
                "segments": {
                    "red":    [min(r0, r1), max(r0, r1)],
                    "yellow": [min(y0, y1), max(y0, y1)],
                    "green":  [min(g0, g1), max(g0, g1)]
                },
                "colors": {
                    "red":    hex_to_rgb(red_hex),
                    "yellow": hex_to_rgb(yellow_hex),
                    "green":  hex_to_rgb(green_hex)
                },
                "schedule": {
                    "yellow_minute": y_min,
                    "red_minute":    r_min,
                    "green_minute":  g_min
                },
                "scheduler_enabled": True
            }
            save_config(new_cfg)
            schedule_from_config()
            message = "✅ Configuration saved, strip re-initialized, and scheduler reloaded."
        except Exception as e:
            message = f"❌ Failed to save: {e}"

    cfg = get_config()
    return render_template("config.html", cfg=cfg, message=message)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if verify_user(username, password):
            session["user"] = username
            flash("Login successful", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("login"))



# ─────────────────────────────────────────────
# App start
# ─────────────────────────────────────────────
if __name__ == "__main__":
    threading.Thread(target=wifi_monitor, daemon=True).start()
    if not scheduler_started:
        scheduler.start()
    schedule_from_config()
    app.run(host="0.0.0.0", port=8080)
