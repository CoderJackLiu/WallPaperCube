### config_manager.py
import os
import json

CONFIG_FILE = "config.json"
DEFAULT_FOLDER = os.path.expanduser("~/Pictures")

class ConfigManager:
    @staticmethod
    def load_config():
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                try:
                    config = json.load(file)
                    if not config.get("last_folder"):
                        raise ValueError("Config missing 'last_folder'")
                    return config
                except Exception as e:
                    print(f"Error loading config: {e}")
        return {"last_folder": DEFAULT_FOLDER, "language": "English"}

    @staticmethod
    def save_config(config):
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file)