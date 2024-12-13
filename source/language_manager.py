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
            "select_language": "Select Language:"
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
            "select_language": "选择语言："
        },
    }

    @staticmethod
    def get_text(language, key, **kwargs):
        return LanguageManager.LANGUAGES[language].get(key, "").format(**kwargs)
