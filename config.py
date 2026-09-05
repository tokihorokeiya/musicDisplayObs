import os
import json
import locale

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def get_default_language():
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            loc_lower = loc.lower()
            if "zh" in loc_lower or "cht" in loc_lower or "tw" in loc_lower or "hk" in loc_lower:
                return "zh_TW"
            elif "ja" in loc_lower or "jp" in loc_lower:
                return "ja"
    except Exception:
        pass
    return "zh_TW" # User is in Traditional Chinese locale (+08:00)

DEFAULT_CONFIG = {
    "port": 11150,
    "language": get_default_language(),
    "resolution_mode": "1920x700",
    "selected_theme": "glassmorphism",
    "autohide_on_pause": False,
    "autohide_delay_seconds": 3,
    "marquee_speed": 40,
    "start_minimized": False
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(data)
                return config
        except Exception as e:
            print(f"Error reading config: {e}")
    return DEFAULT_CONFIG.copy()

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving config: {e}")
