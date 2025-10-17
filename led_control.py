import json, os, threading
import time
from rpi_ws281x import PixelStrip, Color
import board
import neopixel

CONFIG_PATH = "/home/rrpi/statuspage/config.json"

# Globals for a single shared strip
_strip = None
_strip_count = None
_lock = threading.Lock()

def _load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def _save_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=4)

def _ensure_strip():
    """Create/recreate the global strip if LED count changed."""
    global _strip, _strip_count
    cfg = _load_config()
    count = int(cfg["led_count"])
    if _strip is None or _strip_count != count:
        _strip = PixelStrip(count, 18, 800000, 10, False, 150, 0)  # pin=GPIO18
        _strip.begin()
        _strip_count = count
    return _strip, cfg

def set_only(segment_name):
    """Turn off all LEDs, then light the requested segment with its configured color."""
    with _lock:
        strip, cfg = _ensure_strip()
        # clear
        for i in range(_strip_count):
            strip.setPixelColor(i, Color(0, 0, 0))
        # paint segment
        start, end = cfg["segments"][segment_name]
        r, g, b = cfg["colors"][segment_name]
        color = Color(r, g, b)
        for i in range(start, end + 1):
            if 0 <= i < _strip_count:
                strip.setPixelColor(i, color)
        strip.show()

def turn_all_off():
    with _lock:
        strip, cfg = _ensure_strip()
        for i in range(_strip_count):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

def get_config():
    return _load_config()

def save_config(new_cfg):
    """Save and immediately apply new LED configuration."""
    _save_config(new_cfg)
    # Reinitialize the global strip with new count
    global _strip, _strip_count
    _strip = None
    _strip_count = None
    strip, cfg = _ensure_strip()
    # brief visual feedback: white-flash pattern
    for i in range(cfg["led_count"]):
        strip.setPixelColor(i, Color(40, 40, 40))
    strip.show()
    time.sleep(0.3)
    for i in range(cfg["led_count"]):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
