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
from settings_ui import SettingsUI  # 导入拆分后的设置界面逻辑

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
        """加载 OSS 中的壁纸文件，并标记已下载的壁纸"""
        if not self.oss.enabled:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "oss_not_configured"))
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
            self.status_var.set(error_message)

    def _add_cached_mark(self, file_name):
        """为已下载的壁纸动态添加右上角“✔”标记"""
        local_file_name = file_name.split("/")[-1]

        # 遍历所有组件，寻找匹配的缩略图
        for widget in self.oss_scrollable_frame.winfo_children():
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
            self.set_wallpaper(local_path)

            # 更新缓存标记
            self.root.after(0, self._add_cached_mark, file_name)

            # 调试信息
            print(f"Downloaded and marked: {file_name}")

            # 更新状态栏
            self.status_var.set(f"Wallpaper set: {local_path}")
        except Exception as e:
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

        # 首次进入时加载OSS壁纸
        self.select_oss_folder()

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

    def show_images(self, images, scrollable_frame, canvas, on_click):
        """通用图片布局方法"""
        # 清空当前布局
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        # 计算列数
        canvas_width = canvas.winfo_width()
        if canvas_width <= 0:  # 默认列数
            columns = 5
        else:
            columns = max(canvas_width // 120, 1)  # 每张图片约 120px

        # 布局图片
        for index, image_info in enumerate(images):
            thumbnail = image_info.get("thumbnail")  # 直接传入缩略图
            if not thumbnail:
                continue

            # 创建图片Label
            img_label = Label(
                scrollable_frame,
                image=thumbnail,
                text=image_info.get("text", ""),
                compound="top",
                bg="white"
            )
            img_label.photo = thumbnail  # 防止垃圾回收
            img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)
            img_label.bind("<Button-1>", lambda event, info=image_info: on_click(info))

            # 如果壁纸已缓存，调用 _add_cached_mark 动态添加标记
            if image_info.get("is_cached", False):
                print(f"Adding cached mark for: {image_info['text']}")
                self._add_cached_mark(image_info["text"])

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

        # 准备图片数据
        image_data = []
        for image_path in loaded_images:
            thumbnail = ImageManager.generate_thumbnail(image_path)
            if thumbnail:
                image_data.append({
                    "thumbnail": thumbnail,
                    "text": os.path.basename(image_path),
                    "path": image_path
                })

        # 使用通用方法布局图片
        self.show_images(
            images=image_data,
            scrollable_frame=self.local_scrollable_frame,
            canvas=self.local_canvas,
            on_click=lambda info: self.set_wallpaper(info["path"])
        )

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

            with urlopen(thumbnail_url, context=ssl_context) as response:
                img_data = response.read()
                img = Image.open(io.BytesIO(img_data))
                img.thumbnail((100, 100))  # 统一缩略图大小
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
        local_file_name = image_info["path"].split("/")[-1]

        # 创建图片容器
        img_frame = Frame(self.oss_scrollable_frame, bg="white", width=120, height=120)
        img_frame.grid_propagate(False)
        img_frame.grid(row=index // columns, column=index % columns, padx=10, pady=10)

        # 图片 Label
        img_label = Label(
            img_frame,
            image=thumbnail,
            text=local_file_name,
            compound="top",
            bg="white",
            width=100,
            height=100
        )
        img_label.photo = thumbnail
        img_label.cached_mark = None  # 初始化标记属性
        img_label.place(relx=0.5, rely=0.5, anchor="center")
        img_label.bind("<Button-1>", partial(self.download_and_set_wallpaper, image_info["path"]))

        # 如果壁纸已缓存，显示“✔”标记
        if image_info.get("is_cached", False):
            print(f"Adding cached mark during UI creation for: {local_file_name}")
            self._add_cached_mark(image_info["path"])

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
        """显示 OSS 壁纸，并在右上角标记已下载的壁纸"""
        if not self.oss.enabled:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "oss_not_configured"))
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
                self.status_var.set(error_message)
                return

        # 准备图片数据
        image_data = []
        for wallpaper in wallpapers:
            thumbnail = self._fetch_thumbnail(wallpaper["thumbnail"])
            if thumbnail:
                image_data.append({
                    "thumbnail": thumbnail,
                    "text": wallpaper["original"].split("/")[-1],  # 使用 'original'
                    "path": wallpaper["original"],
                    "is_cached": wallpaper.get("is_cached", False)
                })

        # 使用通用方法布局图片
        self.show_images(
            images=image_data,
            scrollable_frame=self.oss_scrollable_frame,
            canvas=self.oss_canvas,
            on_click=lambda info: self.download_and_set_wallpaper(info["path"])
        )

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


    def open_settings(self):
        settings_ui = SettingsUI(self.root, self.config, self.current_language, self)
        settings_ui.open_settings_window()

    def update_ui_texts(self):
        # 更新状态栏
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

        # 更新 Tab 标签
        self.notebook.tab(0, text=LanguageManager.get_text(self.current_language.get(), "local_wallpapers"))
        self.notebook.tab(1, text=LanguageManager.get_text(self.current_language.get(), "oss_wallpapers"))


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
