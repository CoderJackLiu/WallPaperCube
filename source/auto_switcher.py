import os
import threading
from config_manager import ConfigManager
from image_manager import ImageManager
from wallpaper_manager import WallpaperManager

class AutoSwitcher:
    def __init__(self, root, config, folder_path_var, status_var):
        """
        初始化自动切换功能模块。
        :param root: Tkinter 根窗口对象。
        :param config: 配置字典。
        :param folder_path_var: 保存当前文件夹路径的 StringVar 对象。
        :param status_var: 状态栏 StringVar 对象。
        """
        self.root = root
        self.config = config
        self.folder_path_var = folder_path_var
        self.status_var = status_var
        self.auto_switch_task = None

    def start_auto_switch(self, interval):
        """
        开始自动切换壁纸功能。
        :param interval: 自动切换间隔时间（秒）。
        """
        self.stop_auto_switch()  # 确保不会重复启动多个定时任务
        self.auto_switch_task = self.root.after(interval * 1000, self.auto_switch_wallpaper)

    def stop_auto_switch(self):
        """
        停止自动切换壁纸功能。
        """
        if hasattr(self, "auto_switch_task") and self.auto_switch_task:
            self.root.after_cancel(self.auto_switch_task)
            self.auto_switch_task = None

    def auto_switch_wallpaper(self):
        """
        自动切换到下一张壁纸。
        """
        folder = self.folder_path_var.get()
        images = ImageManager.get_images_in_folder(folder)

        if images:
            # 计算当前图片的索引并切换到下一张
            current_image_index = (self.config.get("current_image_index", -1) + 1) % len(images)
            self.config["current_image_index"] = current_image_index
            ConfigManager.save_config(self.config)

            next_image = images[current_image_index]
            success, error = WallpaperManager.set_wallpaper(next_image)

            # 更新状态栏
            if success:
                self.status_var.set(f"Wallpaper set: {os.path.basename(next_image)}")
            else:
                self.status_var.set(f"Failed to set wallpaper: {error}")

        # 继续下一次切换
        interval = self.config.get("auto_switch_interval", 5)
        self.auto_switch_task = self.root.after(interval * 1000, self.auto_switch_wallpaper)
