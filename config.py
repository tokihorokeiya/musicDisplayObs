import os
import sys
import json
import ctypes
import locale

if getattr(sys, 'frozen', False):
    CONFIG_FILE = os.path.join(os.path.dirname(sys.executable), "config.json")
else:
    CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def detect_system_language():
    """Checks the user's operating system display language first. Defaults to 'en' if not matched."""
    try:
        # Check Windows User Default UI Language LCID
        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        primary_lang = lcid & 0x3FF
        lang_map = {
            0x04: "zh_TW", # Traditional Chinese (Taiwan, HK, Macau)
            0x11: "ja",    # Japanese
            0x12: "ko",    # Korean
            0x0A: "es",    # Spanish
            0x0C: "fr",    # French
            0x07: "de",    # German
            0x16: "pt",    # Portuguese
            0x10: "it",    # Italian
            0x19: "ru",    # Russian
            0x21: "id",    # Indonesian
            0x2A: "vi",    # Vietnamese
            0x1E: "th",    # Thai
            0x15: "pl",    # Polish
            0x09: "en",    # English
        }
        if primary_lang in lang_map:
            return lang_map[primary_lang]
    except Exception:
        pass

    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            loc_lower = loc.lower()
            if "zh" in loc_lower or "tw" in loc_lower or "hk" in loc_lower or "cht" in loc_lower:
                return "zh_TW"
            for code in ("ja", "ko", "es", "fr", "de", "pt", "it", "ru", "id", "vi", "th", "pl"):
                if loc_lower.startswith(code):
                    return code
    except Exception:
        pass

    return "en"

DEFAULT_CONFIG = {
    "port": 11150,
    "language": detect_system_language(),
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
