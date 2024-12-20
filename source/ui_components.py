### ui_components.py
from tkinter import Frame, Label, Button, Canvas, filedialog, IntVar, StringVar, ttk
from language_manager import LanguageManager
from image_manager import ImageManager
from wallpaper_manager import WallpaperManager
import math
from config_manager import ConfigManager
import os
from cloud_services.aliyun_oss import AliyunOSS
from cloud_services.oss_config import OSSConfig
from settings_ui import SettingsUI  # 导入拆分后的设置界面逻辑
from auto_switcher import AutoSwitcher
from UI.oss_ui import OSSUIHandler
from UI.local_image_manager import LocalImageManager

class AppUI:
    def __init__(self, root, config, current_language):
        self.oss_page_label = None
        self.oss_pagination_ui = None
        self.pagination_ui = None
        self.local_page_label = None
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
        self.auto_switcher = AutoSwitcher(
            root=self.root,
            config=self.config,
            folder_path_var=self.folder_path,
            status_var=self.status_var
        )
        auto_switch_enabled = self.config.get("auto_switch_enabled", 0)
        auto_switch_interval = self.config.get("auto_switch_interval", 5)

        if auto_switch_enabled and auto_switch_interval >= 5:
            self.auto_switcher.start_auto_switch(auto_switch_interval)
        self.oss_config = OSSConfig.load_config()  # 加载 OSS 配置
        self.oss = None
        self.oss_ui_handler = None
        if self.oss_config["oss_enabled"]:
            self.oss = AliyunOSS(
                self.oss_config["oss_access_key_id"],
                self.oss_config["oss_access_key_secret"],
                self.oss_config["oss_endpoint"],
                self.oss_config["oss_bucket_name"],
            )
            # 初始化 OSSUIHandler
            self.oss_ui_handler = OSSUIHandler(root, self.oss, self.status_var, current_language, self)

        # # 如果 OSS 配置不完整，提示但不影响程序启动
        # if not self.oss.enabled:
        #     print("OSS is not configured or disabled. Skipping OSS features.")
        self.local_image_manager = LocalImageManager(images_per_page=24)
        self.setup_ui()

    def setup_top_frame(self):
        """设置顶部按钮栏"""
        top_frame = Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        self.top_buttons = [
            Label(top_frame, text=LanguageManager.get_text(self.current_language.get(), "wallpaper_folder")),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "select_folder"),
                   command=self.select_folder),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "settings"),
                   command=self.open_settings)
        ]
        # 布局按钮
        self.top_buttons[0].pack(side="left", padx=5)
        self.top_buttons[1].pack(side="left", padx=5)
        self.top_buttons[2].pack(side="right", padx=5)

    def setup_pagination(self):
        """设置底部分页按钮栏"""
        pagination_frame = Frame(self.root)
        pagination_frame.pack(fill="x", padx=10, pady=5)

        pagination_inner_frame = Frame(pagination_frame)
        pagination_inner_frame.pack(anchor="center")

        # self.pagination_buttons = [
        #     Button(pagination_inner_frame, text=LanguageManager.get_text(self.current_language.get(), "previous"),
        #            command=self.previous_page),
        #     Label(pagination_inner_frame, text=""),
        #     Button(pagination_inner_frame, text=LanguageManager.get_text(self.current_language.get(), "next"),
        #            command=self.next_page)
        # ]
        # # 布局分页按钮
        # self.pagination_buttons[0].pack(side="left", padx=10)
        # self.page_label = self.pagination_buttons[1]
        # self.page_label.pack(side="left", padx=10)
        # self.pagination_buttons[2].pack(side="left", padx=10)

    def setup_status_bar(self):
        """设置底部状态栏"""
        Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(side="bottom", fill="x")

    # def setup_oss_tab(self):
    #     """设置 OSS 壁纸 Tab 的内容"""
    #     # 初始化画布
    #     self.oss_canvas = Canvas(self.oss_tab)
    #     self.oss_canvas.pack(fill="both", expand=True, padx=10, pady=5)
    #     self.oss_scrollable_frame = Frame(self.oss_canvas)
    #     self.oss_canvas.create_window((0, 0), window=self.oss_scrollable_frame, anchor="nw")
    #
    #     # 绑定窗口调整事件
    #     self.oss_canvas.bind("<Configure>", lambda event: self.oss_ui_handler.display_oss_images())
    #
    #     # 添加分页按钮
    #     pagination_frame = Frame(self.oss_tab)
    #     pagination_frame.pack(fill="x", pady=10)
    #     self.oss_pagination_ui, self.oss_page_label = self.oss_ui_handler.get_pagination_ui(
    #         pagination_frame, update_callback=self.oss_ui_handler.display_oss_images
    #     )

    # def setup_oss_tab(self):
    #     """设置 OSS 壁纸 Tab 的内容"""
    #     self.oss_ui_handler.setup_oss_ui(self.oss_tab)
    #
    #     # 添加分页按钮
    #     pagination_ui, self.oss_page_label = self.oss_ui_handler.get_pagination_ui(
    #         self.oss_tab, update_callback=self.oss_ui_handler.display_oss_images
    #     )
    #     pagination_ui.pack(fill="x", pady=10)

    # def setup_oss_tab(self):
    #     """设置 OSS 壁纸 Tab 的内容"""
    #     # 初始化画布
    #     self.oss_canvas = Canvas(self.oss_tab)
    #     self.oss_canvas.pack(fill="both", expand=True, padx=10, pady=5)
    #     self.oss_scrollable_frame = Frame(self.oss_canvas)
    #     self.oss_canvas.create_window((0, 0), window=self.oss_scrollable_frame, anchor="nw")
    #
    #     # 绑定窗口调整事件
    #     self.oss_canvas.bind("<Configure>", lambda event: self.oss_ui_handler.display_oss_images())
    #
    #     # 添加分页按钮，与本地壁纸布局保持一致
    #     pagination_frame = Frame(self.oss_tab)
    #     pagination_frame.pack(fill="x", pady=10)
    #     self.oss_pagination_ui, self.oss_page_label = self.oss_ui_handler.get_pagination_ui(
    #         pagination_frame, update_callback=self.oss_ui_handler.display_oss_images
    #     )

    # def setup_local_tab(self):
    #     """设置本地壁纸 Tab 的内容"""
    #     self.local_image_manager.set_folder(self.folder_path.get())
    #
    #     # 初始化画布
    #     self.local_canvas = Canvas(self.local_tab)
    #     self.local_canvas.pack(fill="both", expand=True, padx=10, pady=5)
    #     self.local_scrollable_frame = Frame(self.local_canvas)
    #     self.local_canvas.create_window((0, 0), window=self.local_scrollable_frame, anchor="nw")
    #     self.display_local_images()
    #
    #     # 绑定窗口调整事件
    #     self.local_canvas.bind("<Configure>", self.on_canvas_resize)
    #
    #     # 添加分页按钮
    #     pagination_frame = Frame(self.local_tab)
    #     pagination_frame.pack(fill="x", pady=0)
    #     self.pagination_ui, self.local_page_label = self.local_image_manager.get_pagination_ui(
    #         pagination_frame, update_callback=self.display_local_images
    #     )

    # def setup_oss_tab(self):
    #     """设置 OSS 壁纸 Tab 的内容"""
    #     # 初始化画布
    #     self.oss_canvas = Canvas(self.oss_tab)
    #     self.oss_canvas.pack(fill="both", expand=True, padx=10, pady=5)
    #     self.oss_scrollable_frame = Frame(self.oss_canvas)
    #     self.oss_canvas.create_window((0, 0), window=self.oss_scrollable_frame, anchor="nw")
    #     self.oss_ui_handler.display_oss_images()
    #
    #     # 添加分页按钮
    #     pagination_frame = Frame(self.oss_tab)
    #     pagination_frame.pack(fill="x", pady=10)
    #     self.oss_pagination_ui, self.oss_page_label = self.oss_ui_handler.get_pagination_ui(
    #         pagination_frame, update_callback=self.oss_ui_handler.display_oss_images
    #     )

    def setup_oss_tab(self):
        """设置 OSS 壁纸 Tab 的内容"""
        # 初始化画布
        self.oss_canvas = Canvas(self.oss_tab)
        self.oss_canvas.pack(fill="both", expand=True, padx=10, pady=5)

        self.oss_scrollable_frame = Frame(self.oss_canvas)
        self.oss_canvas.create_window((0, 0), window=self.oss_scrollable_frame, anchor="nw")

        # 绑定窗口调整事件
        self.oss_canvas.bind("<Configure>", lambda event: self.oss_ui_handler.display_oss_images())

        # 添加分页按钮，与本地壁纸布局一致
        pagination_frame = Frame(self.oss_tab)
        pagination_frame.pack(fill="x", pady=10)
        self.oss_pagination_ui, self.oss_page_label = self.oss_ui_handler.get_pagination_ui(
            pagination_frame, update_callback=self.oss_ui_handler.display_oss_images
        )

    def setup_local_tab(self):
        """设置本地壁纸 Tab 的内容"""
        self.local_image_manager.set_folder(self.folder_path.get())

        # 初始化画布
        self.local_canvas = Canvas(self.local_tab)
        self.local_canvas.pack(fill="both", expand=True, padx=10, pady=5)
        self.local_scrollable_frame = Frame(self.local_canvas)
        self.local_canvas.create_window((0, 0), window=self.local_scrollable_frame, anchor="nw")

        # 绑定窗口调整事件
        self.local_canvas.bind("<Configure>", lambda event: self.display_local_images())

        # 添加分页按钮
        pagination_frame = Frame(self.local_tab)
        pagination_frame.pack(fill="x", pady=10)
        self.pagination_ui, self.local_page_label = self.local_image_manager.get_pagination_ui(
            pagination_frame, update_callback=self.display_local_images
        )

    def setup_tabs(self):
        """设置主界面中的 tab 栏"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # 本地文件夹 Tab
        self.local_tab = Frame(self.notebook)
        self.notebook.add(self.local_tab, text="Local Wallpapers")

        # OSS 文件夹 Tab
        self.oss_tab = Frame(self.notebook)
        self.notebook.add(self.oss_tab, text="OSS Wallpapers")

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

    # def show_images(self, images, scrollable_frame, canvas, on_click):
    #     """通用图片布局方法"""
    #     # 清空当前布局
    #     for widget in scrollable_frame.winfo_children():
    #         widget.destroy()
    #
    #     # 计算列数
    #     canvas_width = canvas.winfo_width()
    #     if canvas_width <= 0:  # 默认列数
    #         columns = 5
    #     else:
    #         columns = max(canvas_width // 120, 1)  # 每张图片约 120px
    #
    #     # 布局图片
    #     for index, image_info in enumerate(images):
    #         thumbnail = image_info.get("thumbnail")  # 直接传入缩略图
    #         if not thumbnail:
    #             continue
    #
    #         # 创建图片Label
    #         img_label = Label(
    #             scrollable_frame,
    #             image=thumbnail,
    #             text=image_info.get("text", ""),
    #             compound="top",
    #             bg="white"
    #         )
    #         img_label.photo = thumbnail  # 防止垃圾回收
    #         img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)
    #         img_label.bind("<Button-1>", lambda event, info=image_info: on_click(info))
    #
    #         # 如果壁纸已缓存，调用 _add_cached_mark 动态添加标记
    #         if image_info.get("is_cached", False):
    #             print(f"Adding cached mark for: {image_info['text']}")
    #             self.oss_ui_handler._add_cached_mark(image_info["text"])

    def show_images(self, images, scrollable_frame, canvas, on_click):
        """通用图片布局方法"""
        if scrollable_frame is None:
            raise ValueError("scrollable_frame is None. Ensure it is properly initialized before calling show_images.")

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
            thumbnail = image_info.get("thumbnail")
            if not thumbnail:
                continue

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

    # def display_local_images(self):
    #     """显示本地壁纸"""
    #     image_data = self.local_image_manager.get_image_data()
    #
    #     # 清空当前布局
    #     for widget in self.local_scrollable_frame.winfo_children():
    #         widget.destroy()
    #
    #     # 动态计算列数
    #     canvas_width = self.local_canvas.winfo_width()
    #     if canvas_width <= 0:  # 默认列数
    #         columns = 5
    #     else:
    #         columns = max(canvas_width // 120, 1)  # 每张图片约 120px
    #
    #     # 布局图片
    #     for index, image_info in enumerate(image_data):
    #         thumbnail = image_info.get("thumbnail")
    #         if not thumbnail:
    #             continue
    #
    #         img_label = Label(
    #             self.local_scrollable_frame,
    #             image=thumbnail,
    #             text=image_info.get("text", ""),
    #             compound="top",
    #             bg="white"
    #         )
    #         img_label.photo = thumbnail  # 防止垃圾回收
    #         img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)
    #
    #     # 更新分页状态
    #     if self.local_page_label:
    #         self.local_page_label.config(
    #             text=f"Page {self.local_image_manager.current_page + 1}"
    #         )

    # def display_local_images(self):
    #     """显示本地壁纸"""
    #     image_data = self.local_image_manager.get_image_data()
    #
    #     # 调用 show_images，确保 scrollable_frame 传入正确的值
    #     self.show_images(
    #         images=image_data,
    #         scrollable_frame=self.local_scrollable_frame,
    #         canvas=self.local_canvas,
    #         on_click=lambda info: self.set_wallpaper(info["path"])
    #     )

    def display_local_images(self):
        """显示本地壁纸"""
        image_data = self.local_image_manager.get_image_data()

        # 清空当前布局
        for widget in self.local_scrollable_frame.winfo_children():
            widget.destroy()

        # 动态计算列数
        canvas_width = self.local_canvas.winfo_width()
        if canvas_width <= 0:  # 默认列数
            columns = 5
        else:
            columns = max(canvas_width // 120, 1)  # 每张图片约 120px

        # 布局图片
        for index, image_info in enumerate(image_data):
            thumbnail = image_info.get("thumbnail")
            if not thumbnail:
                continue

            img_label = Label(
                self.local_scrollable_frame,
                image=thumbnail,
                text=image_info.get("text", ""),
                compound="top",
                bg="white"
            )
            img_label.photo = thumbnail  # 防止垃圾回收
            img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)

        # 更新分页状态
        if self.local_page_label:
            self.local_page_label.config(
                text=f"Page {self.local_image_manager.current_page + 1}"
            )

    def display_oss_images(self):
        """显示 OSS 壁纸"""
        self.oss_ui_handler.display_oss_images()

    def display_images(self):
        """根据激活的 Tab 显示壁纸"""
        current_tab = self.notebook.index(self.notebook.select())
        if current_tab == 0:  # 本地壁纸 Tab
            self.display_local_images()
        elif current_tab == 1:  # OSS 壁纸 Tab
            self.oss_ui_handler.display_oss_images()

    def set_wallpaper(self, image_path, event=None):
        """设置下载的壁纸为桌面壁纸"""
        success, error = WallpaperManager.set_wallpaper(image_path)
        if success:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "wallpaper_set_to",
                                                         wallpaper=os.path.basename(image_path)))
        else:
            self.status_var.set(LanguageManager.get_text(self.current_language.get(), "wallpaper_failed", error=error))

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
        # self.pagination_buttons[0].config(text=LanguageManager.get_text(self.current_language.get(), "previous"))
        # self.pagination_buttons[2].config(text=LanguageManager.get_text(self.current_language.get(), "next"))

        # 更新页面标签
        # self.page_label.config(
        #     text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page.get() + 1))

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
        self.display_local_images()
