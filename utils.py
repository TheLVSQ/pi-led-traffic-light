import os, psutil, socket, subprocess, netifaces, time

def get_wifi_info():
    """Return SSID, signal strength, and connection state."""
    try:
        ssid = subprocess.check_output(["iwgetid", "-r"], text=True).strip()
        if not ssid:
            return {"ssid": "Not connected", "signal": 0}
        iwconfig_output = subprocess.check_output(["iwconfig", "wlan0"], text=True)
        if "Signal level" in iwconfig_output:
            signal = int(iwconfig_output.split("Signal level=")[1].split(" ")[0])
        else:
            signal = 0
        return {"ssid": ssid, "signal": signal}
    except subprocess.CalledProcessError:
        return {"ssid": "Not connected", "signal": 0}


def get_ip():
    try:
        return netifaces.ifaddresses("wlan0")[netifaces.AF_INET][0]["addr"]
    except Exception:
        return "N/A"


def get_cpu_temp():
    temps = psutil.sensors_temperatures()
    if temps:
        key = next((k for k in ("cpu-thermal", "cpu_thermal", "thermal_zone0") if k in temps), None)
        if key:
            entry = temps[key][0]
            if hasattr(entry, "current"):
                return round(entry.current, 1)
            elif isinstance(entry, tuple) and len(entry) > 1:
                return round(entry[1], 1)
    try:
        temp = subprocess.check_output(["vcgencmd", "measure_temp"]).decode()
        return float(temp.split("=")[1].split("'")[0])
    except Exception:
        return 0.0


def get_system_info():
    wifi = get_wifi_info()
    info = {
        "hostname": socket.gethostname(),
        "ip_address": get_ip(),
        "wifi_ssid": wifi["ssid"],
        "wifi_signal": wifi["signal"],
        "cpu_temp": get_cpu_temp(),
        "cpu_percent": psutil.cpu_percent(),
        "memory": psutil.virtual_memory(),
        "disk": psutil.disk_usage("/"),
        "uptime": time.strftime("%Hh %Mm %Ss", time.gmtime(time.time() - psutil.boot_time())),
    }
    return info


def reconnect_wifi():
    """Try to reconfigure and restart dhcp."""
    os.system("sudo wpa_cli -i wlan0 reconfigure && sudo systemctl restart dhcpcd")

def clamp_int(n, lo, hi):
    return max(lo, min(hi, int(n)))
