### ui_components.py
from tkinter import Frame, Label, Button, Canvas, Scrollbar, filedialog, IntVar, StringVar, Toplevel, ttk
from language_manager import LanguageManager
from image_manager import ImageManager
from wallpaper_manager import WallpaperManager
import math
from config_manager import ConfigManager
import os
from tkinter import Checkbutton


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
        self.setup_ui()
        self.auto_switch_task = None  # 初始化自动切换任务变量
        auto_switch_enabled = self.config.get("auto_switch_enabled", 0)
        auto_switch_interval = self.config.get("auto_switch_interval", 5)
        if auto_switch_enabled and auto_switch_interval >= 5:
            self.start_auto_switch(auto_switch_interval)

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

    def open_settings(self):
        settings_window = Toplevel(self.root)
        settings_window.title(LanguageManager.get_text(self.current_language.get(), "settings"))

        # 将设置窗口定位到屏幕中心
        settings_width, settings_height = 300, 250
        x_position = self.root.winfo_x() + (self.root.winfo_width() // 2) - (settings_width // 2)
        y_position = self.root.winfo_y() + (self.root.winfo_height() // 2) - (settings_height // 2)
        settings_window.geometry(f"{settings_width}x{settings_height}+{x_position}+{y_position}")

        # 设置窗口为模态窗口
        settings_window.grab_set()
        settings_window.transient(self.root)

        Label(settings_window, text=LanguageManager.get_text(self.current_language.get(), "select_language")).pack(pady=5)
        language_combobox = ttk.Combobox(
            settings_window, values=["English", "Chinese"], state="readonly"
        )
        language_combobox.set(self.current_language.get())
        language_combobox.pack(pady=5)

        # 自动切换开关
        auto_switch_var = IntVar(value=self.config.get("auto_switch_enabled", 0))
        Checkbutton(settings_window, text="Enable Auto-switch", variable=auto_switch_var).pack(pady=5)

        # 自动切换时间间隔
        Label(settings_window, text="Auto-switch interval (seconds):").pack(pady=5)
        interval_var = IntVar(value=self.config.get("auto_switch_interval", 5))
        interval_entry = ttk.Spinbox(
            settings_window, from_=5, to=600, textvariable=interval_var, state="readonly"
        )
        interval_entry.pack(pady=5)

        def save_settings():
            selected_language = language_combobox.get()
            self.current_language.set(selected_language)
            self.config["language"] = selected_language

            # 保存自动切换配置
            self.config["auto_switch_enabled"] = auto_switch_var.get()
            interval = interval_var.get()
            self.config["auto_switch_interval"] = interval
            ConfigManager.save_config(self.config)

            # 启用或停止自动切换逻辑
            if auto_switch_var.get():
                self.start_auto_switch(interval)
            else:
                self.stop_auto_switch()

            self.update_ui_texts()
            settings_window.destroy()

        Button(settings_window, text="Save", command=save_settings).pack(pady=10)

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
