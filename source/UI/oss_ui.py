import os
from tkinter import Frame, Label, Canvas, Scrollbar
from PIL import Image, ImageTk
import threading
from functools import partial
from urllib.request import urlopen
import hashlib
import io
import ssl
from source.language_manager import LanguageManager


class OSSUIHandler:
    def __init__(self, root, oss, status_var, current_language, uiInstance):
        self.root = root
        self.oss = oss
        self.uiInstance = uiInstance
        self.status_var = status_var
        self.current_language = current_language
        self.oss_canvas = None
        self.oss_scrollable_frame = None

    def setup_oss_ui(self, parent_frame):
        """初始化 OSS 的 UI"""
        self.oss_canvas = Canvas(parent_frame)
        self.oss_scrollbar = Scrollbar(parent_frame, orient="vertical", command=self.oss_canvas.yview)

        self.oss_scrollable_frame = Frame(self.oss_canvas)
        self.oss_canvas.create_window((0, 0), window=self.oss_scrollable_frame, anchor="nw")
        self.oss_canvas.configure(yscrollcommand=self.oss_scrollbar.set)

        self.oss_canvas.pack(side="left", fill="both", expand=True)
        self.oss_scrollbar.pack(side="right", fill="y")

        self.oss_canvas.bind("<Configure>", lambda event: self.display_oss_images())

    def _add_cached_mark(self, file_name):
        """为已下载的壁纸动态添加右上角“✔”标记"""
        local_file_name = file_name.split("/")[-1]

        # 遍历所有组件，寻找匹配的缩略图
        for widget in self.uiInstance.oss_ui_handler.oss_scrollable_frame.winfo_children():
            if isinstance(widget, Label) and widget.cget("text") == local_file_name:
                # 确保标记只添加到对应缩略图的右上角
                print(f"Matched widget for file: {local_file_name}")

                # 检查当前缩略图是否已有标记
                if hasattr(widget, "cached_mark") and widget.cached_mark:
                    print(f"Mark already exists for: {local_file_name}")
                    return  # 如果已有标记，直接返回

                # 添加“✔”标记
                cached_label = Label(widget, text="✔", fg="green", bg="white", font=("Arial", 14))
                cached_label.place(relx=1.0, rely=0.0, anchor="ne")  # 定位在右上角
                widget.cached_mark = cached_label  # 保存标记引用，防止重复创建
                print(f"Added ✔ mark for: {local_file_name}")
                return

    def download_and_set_wallpaper(self, file_name, event=None):
        """下载壁纸并设置为桌面壁纸"""
        local_path = os.path.abspath(f"downloads/{file_name.split('/')[-1]}")

        try:
            # 下载壁纸
            if not os.path.exists(local_path):
                self.oss.download_wallpaper(file_name, local_path)

            # 设置壁纸
            self.uiInstance.set_wallpaper(local_path)

            # 更新缓存标记
            self.root.after(0, self._add_cached_mark, file_name)

            # 调试信息
            print(f"Downloaded and marked: {file_name}")

            # 更新状态栏
            msgInfo = LanguageManager.get_text(self.current_language.get(), "wallpaper_set_to",wallpaper={file_name})

            print(f"msgInfo msgInfo msgInfo: {msgInfo}")
            # self.uiInstance.status_var.set(msgInfo)
            # self.uiInstance.status_var.set(f"Wallpaper set: {local_path}")
        except Exception as e:
            self.uiInstance.status_var.set(f"Failed to download or set wallpaper: {e}")

    def display_oss_images(self, wallpapers=None):
        """显示 OSS 壁纸，并在右上角标记已下载的壁纸"""
        if not self.oss.enabled:
            self.uiInstance.status_var.set(LanguageManager.get_text(self.current_language.get(), "oss_not_configured"))
            return

        if wallpapers is None:
            try:
                wallpapers = self.oss.list_wallpapers(prefix="wallpapers/")
                for wallpaper in wallpapers:
                    local_file_name = wallpaper["original"].split("/")[-1]  # 使用 'original'
                    local_path = os.path.abspath(f"downloads/{local_file_name}")
                    wallpaper["is_cached"] = os.path.exists(local_path)
            except Exception as e:
                error_message = LanguageManager.get_text(self.current_language.get(), "oss_load_failed", error=str(e))
                self.uiInstance.status_var.set(error_message)
                return

        # 准备图片数据
        image_data = []
        for wallpaper in wallpapers:
            thumbnail = self.oss.fetch_thumbnail(wallpaper["thumbnail"])
            if thumbnail:
                image_data.append({
                    "thumbnail": thumbnail,
                    "text": wallpaper["original"].split("/")[-1],  # 使用 'original'
                    "path": wallpaper["original"],
                    "is_cached": wallpaper.get("is_cached", False)
                })

        # 使用通用方法布局图片
        self.uiInstance.show_images(
            images=image_data,
            scrollable_frame=self.oss_scrollable_frame,
            canvas=self.oss_canvas,
            on_click=lambda info: self.download_and_set_wallpaper(info["path"])
        )

    def select_oss_folder(self):
        if not self.oss:
            self.uiInstance.status_var.set(LanguageManager.get_text(self.current_language.get(), "oss_not_configured"))
            return
        """加载 OSS 中的壁纸文件，并标记已下载的壁纸"""
        if not self.oss.enabled:
            self.uiInstance.status_var.set(LanguageManager.get_text(self.current_language.get(), "oss_not_configured"))
            return

        try:
            # 获取OSS壁纸列表
            wallpapers = self.oss.list_wallpapers(prefix="wallpapers/")

            # 检查本地缓存，标记哪些壁纸已下载
            for wallpaper in wallpapers:
                local_file_name = wallpaper["original"].split("/")[-1]  # 访问字典的 'original' 键
                local_path = os.path.abspath(f"downloads/{local_file_name}")
                wallpaper["is_cached"] = os.path.exists(local_path)

            # 调试输出
            print("Wallpapers loaded from OSS with cached status:", wallpapers)

            # 显示OSS壁纸
            self.display_oss_images(wallpapers)
        except Exception as e:
            error_message = LanguageManager.get_text(self.current_language.get(), "oss_load_failed", error=str(e))
            self.uiInstance.status_var.set(error_message)
