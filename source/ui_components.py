### ui_components.py
from tkinter import Frame, Label, Button, Canvas, Scrollbar, filedialog, IntVar, StringVar, Toplevel, ttk, Checkbutton, Entry
from language_manager import LanguageManager
from image_manager import ImageManager
from wallpaper_manager import WallpaperManager
import math
from config_manager import ConfigManager
import os
from tkinter import Checkbutton
from cloud_services.aliyun_oss import AliyunOSS
from cloud_services.oss_config import OSSConfig
from functools import partial

class AppUI:
    def __init__(self, root, config, current_language):
        self.root = root
        self.config = config
        self.current_language = current_language

        self.folder_path = StringVar(root, value=config.get("last_folder", ""))
        self.status_var = StringVar(root, value=LanguageManager.get_text(current_language.get(), "ready"))
        self.current_page = IntVar(root, value=0)
        self.images_per_page = 24
        self.top_buttons = []  # 初始化 top_buttons
        self.pagination_buttons = []  # 初始化 pagination_buttons
        self.page_label = None  # 初始化 page_label
        self.scrollable_frame = None  # 初始化 scrollable_frame
        self.auto_switch_task = None  # 初始化自动切换任务变量
        auto_switch_enabled = self.config.get("auto_switch_enabled", 0)
        auto_switch_interval = self.config.get("auto_switch_interval", 5)
        if auto_switch_enabled and auto_switch_interval >= 5:
            self.start_auto_switch(auto_switch_interval)
        self.oss_config = OSSConfig.load_config()  # 加载 OSS 配置
        self.oss = None

        if self.oss_config["oss_enabled"]:
            self.oss = AliyunOSS(
                self.oss_config["oss_access_key_id"],
                self.oss_config["oss_access_key_secret"],
                self.oss_config["oss_endpoint"],
                self.oss_config["oss_bucket_name"],
            )
        self.setup_ui()

    def select_oss_folder(self):
        """加载 OSS 中的壁纸文件。"""
        if not self.oss:
            self.status_var.set("OSS not configured.")
            return

        try:
            wallpapers = self.oss.list_wallpapers(prefix="wallpapers/")
            self.display_oss_images(wallpapers)
        except Exception as e:
            self.status_var.set(f"Failed to load from OSS: {e}")

    def display_oss_images(self, wallpapers):
        """显示 OSS 中的壁纸文件。"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for index, file_name in enumerate(wallpapers):
            img_label = Label(self.scrollable_frame, text=file_name, compound="top", bg="white")
            img_label.grid(row=index // 5, column=index % 5, padx=10, pady=10)
            # 使用 partial 显式绑定 file_name
            img_label.bind("<Button-1>", partial(self.download_and_set_wallpaper, file_name))

    def download_and_set_wallpaper(self, file_name, event=None):
        """下载壁纸并设置为桌面壁纸。"""
        if not self.oss:
            self.status_var.set("OSS not configured.")
            return

        local_path = f"downloads/{file_name.split('/')[-1]}"
        try:
            self.oss.download_wallpaper(file_name, local_path)
            self.set_wallpaper(local_path)
        except Exception as e:
            self.status_var.set(f"Failed to download wallpaper: {e}")

    def setup_ui(self):
        top_frame = Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        self.top_buttons = [
            Label(top_frame, text=LanguageManager.get_text(self.current_language.get(), "wallpaper_folder")),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "select_folder"), command=self.select_folder),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "settings"), command=self.open_settings)
        ]
        # 确保按钮按照索引顺序正确布局
        self.top_buttons[0].pack(side="left", padx=5)
        self.top_buttons[1].pack(side="left", padx=5)
        self.top_buttons[2].pack(side="right", padx=5)

        # 继续原有布局逻辑
        self.canvas_frame = Frame(self.root)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = Canvas(self.canvas_frame)
        self.scrollbar = Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = Frame(self.canvas)  # 确保 scrollable_frame 初始化
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self.on_canvas_resize)

        pagination_frame = Frame(self.root)
        pagination_frame.pack(fill="x", padx=10, pady=5)

        pagination_inner_frame = Frame(pagination_frame)
        pagination_inner_frame.pack(anchor="center")

        self.pagination_buttons = [
            Button(pagination_inner_frame, text=LanguageManager.get_text(self.current_language.get(), "previous"), command=self.previous_page),
            Label(pagination_inner_frame, text=""),
            Button(pagination_inner_frame, text=LanguageManager.get_text(self.current_language.get(), "next"), command=self.next_page)
        ]

        self.pagination_buttons[0].pack(side="left", padx=10)
        self.page_label = self.pagination_buttons[1]
        self.page_label.pack(side="left", padx=10)
        self.pagination_buttons[2].pack(side="left", padx=10)

        Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(side="bottom", fill="x")
        self.display_images()

    def display_images(self):
        folder = self.folder_path.get()
        images = ImageManager.get_images_in_folder(folder)
        total_images = len(images)
        max_page = math.ceil(total_images / self.images_per_page) - 1

        if self.current_page.get() > max_page:
            self.current_page.set(max_page)

        start_index = self.current_page.get() * self.images_per_page
        end_index = min(start_index + self.images_per_page, total_images)
        loaded_images = [(image_path, ImageManager.generate_thumbnail(image_path)) for image_path in images[start_index:end_index]]

        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        columns = max(self.canvas.winfo_width() // 120, 1)

        for index, (image_path, thumbnail) in enumerate(loaded_images):
            img_label = Label(self.scrollable_frame, image=thumbnail, text=os.path.basename(image_path), compound="top", bg="white")
            img_label.photo = thumbnail
            img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)
            img_label.bind("<Button-1>", lambda event, path=image_path: self.set_wallpaper(path))

        self.page_label.config(text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page.get() + 1))

    def set_wallpaper(self, image_path):
        success, error = WallpaperManager.set_wallpaper(image_path)
        if success:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "wallpaper_set_to", wallpaper=os.path.basename(image_path)))
        else:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "wallpaper_failed", error=error))

    def start_auto_switch(self, interval):
        """开始自动切换壁纸功能。"""
        self.stop_auto_switch()  # 确保不会重复启动多个定时任务
        self.auto_switch_task = self.root.after(interval * 1000, self.auto_switch_wallpaper)

    def stop_auto_switch(self):
        """停止自动切换壁纸功能。"""
        if hasattr(self, "auto_switch_task") and self.auto_switch_task:
            self.root.after_cancel(self.auto_switch_task)
            self.auto_switch_task = None

    def auto_switch_wallpaper(self):
        """自动切换到下一张壁纸。"""
        folder = self.folder_path.get()
        images = ImageManager.get_images_in_folder(folder)

        if images:
            # 计算当前图片的索引并切换到下一张
            current_image_index = (self.config.get("current_image_index", -1) + 1) % len(images)
            self.config["current_image_index"] = current_image_index
            ConfigManager.save_config(self.config)

            next_image = images[current_image_index]
            self.set_wallpaper(next_image)

        # 继续下一次切换
        interval = self.config.get("auto_switch_interval", 5)
        self.auto_switch_task = self.root.after(interval * 1000, self.auto_switch_wallpaper)

    def select_folder(self):
        folder = filedialog.askdirectory(title=LanguageManager.get_text(self.current_language.get(), "select_folder"))
        if folder:
            self.folder_path.set(folder)
            self.config["last_folder"] = folder
            ConfigManager.save_config(self.config)
            self.current_page.set(0)
            self.display_images()

    from tkinter import Frame, Label, Button, IntVar, StringVar, Toplevel, ttk, Entry, Checkbutton
    def _create_general_settings(self, notebook):
        general_frame = Frame(notebook)

        # 语言选择
        Label(general_frame, text=LanguageManager.get_text(self.current_language.get(), "select_language")).pack(pady=5)
        language_combobox = ttk.Combobox(
            general_frame, values=["English", "Chinese"], state="readonly"
        )
        language_combobox.set(self.current_language.get())
        language_combobox.pack(pady=5)
        self.language_combobox = language_combobox  # 存储引用以便保存时访问

        # 自动切换设置
        auto_switch_var = IntVar(value=self.config.get("auto_switch_enabled", 0))
        Checkbutton(general_frame, text=LanguageManager.get_text(self.current_language.get(), "enable_auto_switch"), variable=auto_switch_var).pack(pady=5)
        self.auto_switch_var = auto_switch_var  # 存储引用以便保存时访问

        interval_var = IntVar(value=self.config.get("auto_switch_interval", 5))
        Label(general_frame, text=LanguageManager.get_text(self.current_language.get(), "auto_switch_interval")).pack(pady=5)
        interval_entry = ttk.Spinbox(
            general_frame, from_=5, to=600, textvariable=interval_var, state="readonly"
        )
        interval_entry.pack(pady=5)
        self.interval_var = interval_var  # 存储引用以便保存时访问

        return general_frame

    def _create_oss_settings(self, notebook):
        oss_frame = Frame(notebook)

        oss_enabled_var = IntVar(value=self.oss_config.get("oss_enabled", 0))
        Checkbutton(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "enable_oss"), variable=oss_enabled_var).pack(pady=5)
        self.oss_enabled_var = oss_enabled_var  # 存储引用以便保存时访问

        access_key_var = StringVar(value=self.oss_config.get("oss_access_key_id", ""))
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "access_key_id")).pack(pady=5)
        Entry(oss_frame, textvariable=access_key_var).pack(pady=5)
        self.access_key_var = access_key_var

        secret_key_var = StringVar(value=self.oss_config.get("oss_access_key_secret", ""))
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "access_key_secret")).pack(pady=5)
        Entry(oss_frame, textvariable=secret_key_var, show="*").pack(pady=5)
        self.secret_key_var = secret_key_var

        endpoint_var = StringVar(value=self.oss_config.get("oss_endpoint", ""))
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "endpoint")).pack(pady=5)
        Entry(oss_frame, textvariable=endpoint_var).pack(pady=5)
        self.endpoint_var = endpoint_var

        bucket_var = StringVar(value=self.oss_config.get("oss_bucket_name", ""))
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "bucket_name")).pack(pady=5)
        Entry(oss_frame, textvariable=bucket_var).pack(pady=5)
        self.bucket_var = bucket_var

        return oss_frame

    def _save_settings(self, settings_window):
        # 保存语言设置
        selected_language = self.language_combobox.get()
        self.current_language.set(selected_language)
        self.config["language"] = selected_language

        # 保存 OSS 配置
        self.oss_config.update({
            "oss_enabled": self.oss_enabled_var.get(),
            "oss_access_key_id": self.access_key_var.get(),
            "oss_access_key_secret": self.secret_key_var.get(),
            "oss_endpoint": self.endpoint_var.get(),
            "oss_bucket_name": self.bucket_var.get(),
        })
        OSSConfig.save_config(self.oss_config)

        # 保存通用配置
        self.config["auto_switch_enabled"] = self.auto_switch_var.get()
        self.config["auto_switch_interval"] = self.interval_var.get()
        ConfigManager.save_config(self.config)

        # 更新自动切换逻辑
        if self.auto_switch_var.get():
            self.start_auto_switch(self.interval_var.get())
        else:
            self.stop_auto_switch()

        # 更新 UI 文本
        self.update_ui_texts()
        settings_window.destroy()

    def open_settings(self):
        settings_window = Toplevel(self.root)
        settings_window.title(LanguageManager.get_text(self.current_language.get(), "settings"))
        settings_window.grab_set()
        settings_window.transient(self.root)

        # 将窗口定位到主窗口中心
        settings_width, settings_height = 500, 400
        x_position = self.root.winfo_x() + (self.root.winfo_width() // 2) - (settings_width // 2)
        y_position = self.root.winfo_y() + (self.root.winfo_height() // 2) - (settings_height // 2)
        settings_window.geometry(f"{settings_width}x{settings_height}+{x_position}+{y_position}")

        # 创建 Notebook（侧边栏选项卡）
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 添加各个选项卡
        general_frame = self._create_general_settings(notebook)
        oss_frame = self._create_oss_settings(notebook)

        notebook.add(general_frame, text=LanguageManager.get_text(self.current_language.get(), "general_settings"))
        notebook.add(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "oss_settings"))

        # 保存按钮
        Button(settings_window, text=LanguageManager.get_text(self.current_language.get(), "save_settings"), command=lambda: self._save_settings(settings_window)).pack(
            pady=10)

    def update_ui_texts(self):
        self.status_var.set(LanguageManager.get_text(self.current_language.get(), "ready"))

        # 更新顶部按钮
        self.top_buttons[0].config(text=LanguageManager.get_text(self.current_language.get(), "wallpaper_folder"))
        self.top_buttons[1].config(text=LanguageManager.get_text(self.current_language.get(), "select_folder"))
        self.top_buttons[2].config(text=LanguageManager.get_text(self.current_language.get(), "settings"))

        # 更新分页按钮
        self.pagination_buttons[0].config(text=LanguageManager.get_text(self.current_language.get(), "previous"))
        self.pagination_buttons[2].config(text=LanguageManager.get_text(self.current_language.get(), "next"))

        # 更新页面标签
        self.page_label.config(text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page.get() + 1))

    def next_page(self):
        folder = self.folder_path.get()
        images = ImageManager.get_images_in_folder(folder)
        max_page = math.ceil(len(images) / self.images_per_page) - 1
        if self.current_page.get() < max_page:
            self.current_page.set(self.current_page.get() + 1)
            self.display_images()

    def previous_page(self):
        if self.current_page.get() > 0:
            self.current_page.set(self.current_page.get() - 1)
            self.display_images()

    def on_canvas_resize(self, event):
        self.display_images()
