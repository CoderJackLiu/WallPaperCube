### main.py
from tkinter import Tk, StringVar
from config_manager import ConfigManager
from ui_components import AppUI
from Auth.user_info_manager import UserInfoManager


# Initialize main application
def main():
    windows_width = 800
    windows_height = 560
    root = Tk()
    root.title("Wallpaper Changer")
    root.geometry(f"{windows_width}x{windows_height}")  # 设置窗口初始化大小

    # 将窗口位置调整为屏幕中央
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x_position = (screen_width // 2) - (windows_width // 2)
    y_position = (screen_height // 2) - (windows_height // 2)
    root.geometry(f"{windows_width}x{windows_height}+{x_position}+{y_position}")

    user_info_manager = UserInfoManager()
    user_info = user_info_manager.load_user_info()  # 在主程序中加载用户信息

    if user_info:
        print(f"已加载用户信息: {user_info}")
    else:
        print("未检测到用户信息")

    config = ConfigManager.load_config()
    current_language = StringVar(root, value=config.get("language", "English"))

    app_ui = AppUI(root, config, current_language)
    root.mainloop()


if __name__ == "__main__":
    main()
