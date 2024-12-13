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
import threading
from PIL import Image, ImageTk
import io
import ssl
from urllib.request import urlopen
import traceback
from concurrent.futures import ThreadPoolExecutor
import hashlib

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
        # # 如果 OSS 配置不完整，提示但不影响程序启动
        # if not self.oss.enabled:
        #     print("OSS is not configured or disabled. Skipping OSS features.")

        self.setup_ui()

    def select_oss_folder(self):
        """加载 OSS 中的壁纸文件。"""
        if not self.oss.enabled:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "oss_not_configured"))
            return

        try:
            wallpapers = self.oss.list_wallpapers(prefix="wallpapers/")
            self.display_oss_images(wallpapers)  # 传递获取的壁纸列表
        except Exception as e:
            error_message = LanguageManager.get_text(self.current_language.get(), "oss_load_failed", error=str(e))
            self.status_var.set(error_message)

    from functools import partial

    def download_and_set_wallpaper(self, file_name, event=None):
        """下载壁纸并设置为桌面壁纸"""
        # 获取下载的完整文件路径
        local_path = os.path.abspath(f"downloads/{file_name.split('/')[-1]}")

        try:
            # 检查文件是否已存在
            if not os.path.exists(local_path):
                # 如果文件不存在，则从 OSS 下载
                self.oss.download_wallpaper(file_name, local_path)

            # 应用壁纸
            self.set_wallpaper(local_path)

            # 更新状态栏
            self.status_var.set(f"Wallpaper set: {local_path}")
        except Exception as e:
            # 更新状态栏，显示下载错误
            self.status_var.set(f"Failed to download or set wallpaper: {e}")

    def setup_top_frame(self):
        """设置顶部按钮栏"""
        top_frame = Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        self.top_buttons = [
            Label(top_frame, text=LanguageManager.get_text(self.current_language.get(), "wallpaper_folder")),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "select_folder"), command=self.select_folder),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "settings"), command=self.open_settings)
        ]
        # 布局按钮
        self.top_buttons[0].pack(side="left", padx=5)
        self.top_buttons[1].pack(side="left", padx=5)
        self.top_buttons[2].pack(side="right", padx=5)

    def setup_canvas(self):
        """设置主画布区域"""
        self.canvas_frame = Frame(self.root)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.canvas = Canvas(self.canvas_frame)
        self.scrollbar = Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)

        self.scrollable_frame = Frame(self.canvas)  # 初始化 scrollable_frame
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self.on_canvas_resize)

    def setup_pagination(self):
        """设置底部分页按钮栏"""
        pagination_frame = Frame(self.root)
        pagination_frame.pack(fill="x", padx=10, pady=5)

        pagination_inner_frame = Frame(pagination_frame)
        pagination_inner_frame.pack(anchor="center")

        self.pagination_buttons = [
            Button(pagination_inner_frame, text=LanguageManager.get_text(self.current_language.get(), "previous"), command=self.previous_page),
            Label(pagination_inner_frame, text=""),
            Button(pagination_inner_frame, text=LanguageManager.get_text(self.current_language.get(), "next"), command=self.next_page)
        ]
        # 布局分页按钮
        self.pagination_buttons[0].pack(side="left", padx=10)
        self.page_label = self.pagination_buttons[1]
        self.page_label.pack(side="left", padx=10)
        self.pagination_buttons[2].pack(side="left", padx=10)

    def setup_status_bar(self):
        """设置底部状态栏"""
        Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(side="bottom", fill="x")

    def setup_oss_tab(self):
        """初始化 OSS 壁纸的 Tab"""
        self.oss_canvas = Canvas(self.oss_tab)
        self.oss_scrollbar = Scrollbar(self.oss_tab, orient="vertical", command=self.oss_canvas.yview)

        self.oss_scrollable_frame = Frame(self.oss_canvas)
        self.oss_canvas.create_window((0, 0), window=self.oss_scrollable_frame, anchor="nw")
        self.oss_canvas.configure(yscrollcommand=self.oss_scrollbar.set)

        self.oss_canvas.pack(side="left", fill="both", expand=True)
        self.oss_scrollbar.pack(side="right", fill="y")

        self.oss_canvas.bind("<Configure>", lambda event: self.display_oss_images())

    def setup_local_tab(self):
        """初始化本地壁纸的 Tab"""
        self.local_canvas = Canvas(self.local_tab)
        self.local_scrollbar = Scrollbar(self.local_tab, orient="vertical", command=self.local_canvas.yview)

        self.local_scrollable_frame = Frame(self.local_canvas)
        self.local_canvas.create_window((0, 0), window=self.local_scrollable_frame, anchor="nw")
        self.local_canvas.configure(yscrollcommand=self.local_scrollbar.set)

        self.local_canvas.pack(side="left", fill="both", expand=True)
        self.local_scrollbar.pack(side="right", fill="y")

        self.local_canvas.bind("<Configure>", lambda event: self.display_local_images())

    def setup_tabs(self):
        """设置主界面中的 tab 栏"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # 本地文件夹 Tab
        self.local_tab = Frame(self.notebook)
        self.notebook.add(self.local_tab, text=LanguageManager.get_text(self.current_language.get(), "local_wallpapers"))

        # OSS 文件夹 Tab
        self.oss_tab = Frame(self.notebook)
        self.notebook.add(self.oss_tab, text=LanguageManager.get_text(self.current_language.get(), "oss_wallpapers"))

        # 分别初始化两个 Tab 的内容
        self.setup_local_tab()
        self.setup_oss_tab()

    def setup_ui(self):
        """设置主界面布局"""
        self.setup_top_frame()
        self.setup_tabs()  # 新增方法
        self.setup_pagination()
        self.setup_status_bar()
        self.display_images()  # 默认显示本地壁纸

    def display_local_images(self):
        """显示本地壁纸，支持分页和横向自适应布局"""
        folder = self.folder_path.get()
        images = ImageManager.get_images_in_folder(folder)

        # 计算分页信息
        total_images = len(images)
        max_page = math.ceil(total_images / self.images_per_page) - 1
        if self.current_page.get() > max_page:
            self.current_page.set(max_page)

        start_index = self.current_page.get() * self.images_per_page
        end_index = min(start_index + self.images_per_page, total_images)
        loaded_images = images[start_index:end_index]

        # 清空当前布局
        for widget in self.local_scrollable_frame.winfo_children():
            widget.destroy()

        # 计算列数
        canvas_width = self.local_canvas.winfo_width()
        if canvas_width <= 0:  # 默认列数
            columns = 5
        else:
            columns = max(canvas_width // 120, 1)  # 每张图片约 120px

        # 布局图片
        for index, image_path in enumerate(loaded_images):
            thumbnail = ImageManager.generate_thumbnail(image_path)
            if thumbnail:
                img_label = Label(
                    self.local_scrollable_frame,
                    image=thumbnail,
                    text=os.path.basename(image_path),
                    compound="top",
                    bg="white"
                )
                img_label.photo = thumbnail  # 防止垃圾回收
                img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)
                img_label.bind("<Button-1>", lambda event, path=image_path: self.set_wallpaper(path))

        # 更新分页状态
        self.page_label.config(text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page.get() + 1))

    def _fetch_oss_wallpapers(self):
        """从 OSS 获取壁纸列表"""
        try:
            return self.oss.list_wallpapers(prefix="wallpapers/")
        except Exception as e:
            error_message = LanguageManager.get_text(self.current_language.get(), "oss_load_failed", error=str(e))
            self.status_var.set(error_message)
            return None

    def _fetch_thumbnail(self, thumbnail_url):
        """从远程或本地获取缩略图"""
        try:
            # 生成本地缓存路径
            hashed_filename = hashlib.md5(thumbnail_url.encode()).hexdigest() + ".png"
            cached_thumbnail_path = os.path.join("thumbnails", hashed_filename)

            # 如果缓存存在，直接使用
            if os.path.exists(cached_thumbnail_path):
                return ImageTk.PhotoImage(Image.open(cached_thumbnail_path))

            # 否则从远程下载
            os.makedirs("thumbnails", exist_ok=True)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            with urlopen(thumbnail_url, context=ssl_context, timeout=10) as response:  # 设置超时时间
                img_data = response.read()
                img = Image.open(io.BytesIO(img_data))
                img.save(cached_thumbnail_path)  # 保存到本地缓存
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error fetching thumbnail: {e}")
            return None

    def _calculate_columns(self):
        """动态计算图片列数"""
        canvas_width = self.oss_canvas.winfo_width()
        return max(canvas_width // 120, 1) if canvas_width > 0 else 5

    def _load_and_display_image(self, index, image_info, columns):
        """异步加载和显示单张图片"""
        try:
            # 调用实例方法获取缩略图
            thumbnail = self._fetch_thumbnail(image_info["thumbnail"])
            # UI 更新必须在主线程中完成
            threading.Thread(target=self._create_image_ui, args=(index, image_info, thumbnail, columns)).start()
        except Exception as e:
            print(f"Error loading image {image_info['thumbnail']}: {e}")

    def _create_image_ui(self, index, image_info, thumbnail, columns):
        """创建图片的 UI 和标记"""
        # 获取本地缓存路径
        local_file_name = image_info["original"].split("/")[-1]
        local_path = os.path.abspath(f"downloads/{local_file_name}")

        # 检查是否已缓存
        is_cached = os.path.exists(local_path)

        # 创建图片容器
        img_frame = Frame(self.oss_scrollable_frame, bg="white")
        img_frame.grid(row=index // columns, column=index % columns, padx=10, pady=10)

        # 缩略图
        img_label = Label(
            img_frame,
            image=thumbnail,
            text=local_file_name,
            compound="top",
            bg="white"
        )
        img_label.photo = thumbnail  # 防止垃圾回收
        img_label.pack(side="top", padx=5, pady=5)
        img_label.bind("<Button-1>", partial(self.download_and_set_wallpaper, image_info["original"]))

        # 如果已缓存，添加“✔”标记
        if is_cached:
            cached_label = Label(img_frame, text="✔", fg="green", bg="white", font=("Arial", 12))
            cached_label.pack(side="bottom", padx=5)

    def _process_and_display_image(self, index, image_info, columns):
        """后台处理缩略图并更新 UI"""
        try:
            # 调用实例方法获取缩略图
            thumbnail = self._fetch_thumbnail(image_info["thumbnail"])

            # UI 更新必须在主线程中完成
            self.root.after(0, self._create_image_ui, index, image_info, thumbnail, columns)
        except Exception as e:
            print(f"Error loading image {image_info['thumbnail']}: {e}")

    def display_oss_images(self, wallpapers=None):
        """显示 OSS 壁纸主方法"""
        if not self.oss.enabled:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "oss_not_configured"))
            return

        if wallpapers is None:
            wallpapers = self._fetch_oss_wallpapers()
            if wallpapers is None:
                return

        # 清空现有的图片显示区域
        for widget in self.oss_scrollable_frame.winfo_children():
            widget.destroy()

        # 动态计算列数
        columns = self._calculate_columns()

        # 使用线程池处理图片加载
        self.executor = ThreadPoolExecutor(max_workers=10)  # 增大线程池大小
        for index, image_info in enumerate(wallpapers):
            self.executor.submit(self._process_and_display_image, index, image_info, columns)

    def display_images(self):
        """根据激活的 Tab 显示壁纸"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:  # 本地壁纸 Tab
            self.display_local_images()
        elif current_tab == 1:  # OSS 壁纸 Tab
            self.display_oss_images()

    def set_wallpaper(self, image_path, event=None):
        """设置下载的壁纸为桌面壁纸"""
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
        """切换到下一页"""
        folder = self.folder_path.get()
        images = ImageManager.get_images_in_folder(folder)
        max_page = math.ceil(len(images) / self.images_per_page) - 1
        if self.current_page.get() < max_page:
            self.current_page.set(self.current_page.get() + 1)
            self.display_local_images()

    def previous_page(self):
        """切换到上一页"""
        if self.current_page.get() > 0:
            self.current_page.set(self.current_page.get() - 1)
            self.display_local_images()

    def on_canvas_resize(self, event):
        """窗口大小变化时更新布局"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:  # 本地壁纸 Tab
            self.display_local_images()
        elif current_tab == 1:  # OSS 壁纸 Tab
            self.display_oss_images()
