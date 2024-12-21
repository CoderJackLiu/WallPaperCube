import os
import json

OSS_CONFIG_FILE = "oss_config.json"

DEFAULT_OSS_CONFIG = {
    "oss_enabled": False,
    "oss_access_key_id": "",
    "oss_access_key_secret": "",
    "oss_endpoint": "",
    "oss_bucket_name": "",
}


class OSSConfig:
    @staticmethod
    def load_config():
        """加载 OSS 配置"""
        if os.path.exists(OSS_CONFIG_FILE):
            with open(OSS_CONFIG_FILE, "r") as file:
                try:
                    return json.load(file)
                except Exception as e:
                    print(f"Error loading OSS config: {e}")
        return DEFAULT_OSS_CONFIG

    @staticmethod
    def save_config(config):
        """保存 OSS 配置"""
        with open(OSS_CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)
