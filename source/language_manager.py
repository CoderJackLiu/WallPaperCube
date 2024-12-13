class LanguageManager:
    LANGUAGES = {
        "English": {
            "select_folder": "Select Folder",
            "settings": "Settings",
            "wallpaper_folder": "Wallpaper Folder:",
            "previous": "Previous",
            "next": "Next",
            "page": "Page {page}",
            "ready": "Ready",
            "wallpaper_set_to": "Wallpaper set to: {wallpaper}",
            "wallpaper_failed": "Failed to set wallpaper: {error}",
            "select_language": "Select Language:",
            "oss_settings": "OSS Settings",
            "enable_oss": "Enable OSS",
            "access_key_id": "Access Key ID",
            "access_key_secret": "Access Key Secret",
            "endpoint": "Endpoint",
            "bucket_name": "Bucket Name",
            "general_settings": "General Settings",
            "enable_auto_switch": "Enable Auto-switch",
            "auto_switch_interval": "Switch Interval (seconds):",
            "save_settings": "Save Settings"
        },
        "Chinese": {
            "select_folder": "选择文件夹",
            "settings": "设置",
            "wallpaper_folder": "壁纸文件夹：",
            "previous": "上一页",
            "next": "下一页",
            "page": "第{page}页",
            "ready": "准备完成",
            "wallpaper_set_to": "壁纸已设置为：{wallpaper}",
            "wallpaper_failed": "设置壁纸失败：{error}",
            "select_language": "选择语言：",
            "oss_settings": "OSS 设置",
            "enable_oss": "启用 OSS",
            "access_key_id": "访问密钥 ID",
            "access_key_secret": "访问密钥 Secret",
            "endpoint": "节点",
            "bucket_name": "存储桶名称",
            "general_settings": "通用设置",
            "enable_auto_switch": "启用自动切换",
            "auto_switch_interval": "切换间隔（秒）：",
            "save_settings": "保存设置"
        },
    }

    @staticmethod
    def get_text(language, key, **kwargs):
        return LanguageManager.LANGUAGES[language].get(key, "").format(**kwargs)
