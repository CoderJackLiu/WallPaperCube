### main.py
from tkinter import Tk, StringVar
from config_manager import ConfigManager
from language_manager import LanguageManager
from wallpaper_manager import WallpaperManager
from ui_components import AppUI

# Initialize main application
def main():
    root = Tk()
    root.title("Wallpaper Changer")
    root.geometry("800x600")  # 设置窗口初始化大小

    # 将窗口位置调整为屏幕中央
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width // 2) - (800 // 2)
    y_position = (screen_height // 2) - (600 // 2)
    root.geometry(f"800x600+{x_position}+{y_position}")

    config = ConfigManager.load_config()
    current_language = StringVar(root, value=config.get("language", "English"))

    app_ui = AppUI(root, config, current_language)
    root.mainloop()

if __name__ == "__main__":
    main()