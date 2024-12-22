### ui_components.py
import io
import json
from tkinter import Frame, Label, Button, Canvas, filedialog, IntVar, StringVar, ttk, Menu

import requests

from language_manager import LanguageManager
from wallpaper_manager import WallpaperManager
from config_manager import ConfigManager
import os
from cloud_services.aliyun_oss import AliyunOSS
from cloud_services.oss_config import OSSConfig
from settings_ui import SettingsUI  # 导入拆分后的设置界面逻辑
from auto_switcher import AutoSwitcher
from UI.oss_ui import OSSUIHandler
from UI.local_image_manager import LocalImageManager
from Auth.github_auth import GitHubAuth

import pickle
from cryptography.fernet import Fernet

from Auth.user_info_manager import UserInfoManager

class AppUI:
    def __init__(self, root, config, current_language):
        self.oss_page_label = None
        self.oss_pagination_ui = None
        self.pagination_ui = None
        self.local_page_label = None
        self.root = root
        self.config = config
        self.current_language = current_language
        self.github_auth = GitHubAuth()  # 初始化 GitHub 鉴权模块
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
        self.user_info_manager = UserInfoManager()
        self.user_info = self.user_info_manager.load_user_info()  # 加载用户信息

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
        self.local_image_manager = LocalImageManager(current_language,images_per_page=24)
        self.setup_ui()
        if self.user_info:
            print(f"已加载用户信息: {self.user_info}")
            self.oss_ui_handler.update_uid(self.user_info["id"])
        else:
            print("未检测到用户信息")

    def setup_top_frame(self):
        """设置顶部按钮栏"""
        top_frame = Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        # 壁纸文件夹和选择文件夹按钮
        self.top_buttons = [
            Label(top_frame, text=LanguageManager.get_text(self.current_language.get(), "wallpaper_folder")),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "select_folder"),
                   command=self.select_folder),
            Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "settings"),
                   command=self.open_settings)
        ]

        # 布局静态按钮
        self.top_buttons[0].pack(side="left", padx=5)
        self.top_buttons[1].pack(side="left", padx=5)
        self.top_buttons[2].pack(side="right", padx=5)

        # 动态的登录按钮或头像按钮
        self.login_button = Button(top_frame, text=LanguageManager.get_text(self.current_language.get(), "login"),
                                   command=self.github_login)
        self.avatar_button = Button(top_frame, command=self.show_avatar_menu)
        self.avatar_menu = Menu(self.root, tearoff=0)
        self.avatar_menu.add_command(label=LanguageManager.get_text(self.current_language.get(), "logout"),
                                     command=self.logout)

        # 根据登录状态切换按钮
        if self.user_info:  # 已登录
            self.update_to_avatar_button()
        else:  # 未登录
            self.update_to_login_button()

    def setup_pagination(self):
        """设置底部分页按钮栏"""
        pagination_frame = Frame(self.root)
        pagination_frame.pack(fill="x", padx=10, pady=5)

        pagination_inner_frame = Frame(pagination_frame)
        pagination_inner_frame.pack(anchor="center")

    def setup_status_bar(self):
        """设置底部状态栏"""
        Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(side="bottom", fill="x")

    def setup_oss_tab(self):
        """设置 OSS 壁纸 Tab 的内容"""
        # 初始化画布
        self.oss_canvas = Canvas(self.oss_tab)
        self.oss_canvas.pack(fill="both", expand=True, padx=10, pady=5)

        self.oss_scrollable_frame = Frame(self.oss_canvas)
        self.oss_canvas.create_window((0, 0), window=self.oss_scrollable_frame, anchor="nw")

        # 绑定窗口调整事件
        self.oss_canvas.bind("<Configure>", lambda event: self.oss_ui_handler.display_oss_images())

        self.oss_ui_handler.oss_scrollable_frame = self.oss_scrollable_frame
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

    def update_to_login_button(self):
        """切换为登录按钮"""
        self.avatar_button.pack_forget()
        self.login_button.pack(side="right", padx=5)

    def update_to_avatar_button(self):
        """切换为头像按钮，并设置固定大小为 20x20"""
        # 如果用户有头像，加载头像图片
        avatar_url = self.user_info.get("avatar_url")
        if avatar_url:
            self.avatar_photo = self.fetch_avatar_image(avatar_url)
            self.avatar_button.config(image=self.avatar_photo, width=20, height=20)  # 固定按钮大小为 20x20
        else:
            self.avatar_button.config(text="Avatar", width=5, height=1)  # 无头像时显示文本

        self.login_button.pack_forget()
        self.avatar_button.pack(side="right", padx=5)

    def fetch_avatar_image(self, url):
        """从 URL 获取头像图片并调整大小为 20x20"""
        try:
            from urllib.request import urlopen
            from PIL import Image, ImageTk
            with urlopen(url) as response:
                avatar_image = Image.open(io.BytesIO(response.read()))
                avatar_image = avatar_image.resize((20, 20))  # 缩放头像大小为 20x20
                return ImageTk.PhotoImage(avatar_image)
        except Exception as e:
            print(f"头像加载失败: {e}")
            return None

    def show_avatar_menu(self):
        """显示头像菜单"""
        self.avatar_menu.post(
            self.avatar_button.winfo_rootx(),
            self.avatar_button.winfo_rooty() + self.avatar_button.winfo_height()
        )

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
            # 如果壁纸已缓存，调用 _add_cached_mark 动态添加标记
            if image_info.get("is_cached", False):
                print(f"Adding cached mark for: {image_info['text']}")
                self.oss_ui_handler._add_cached_mark(image_info["text"])

    def display_local_images(self):
        """显示本地壁纸"""
        image_data = self.local_image_manager.get_image_data()

        # 调用 show_images，确保 scrollable_frame 传入正确的值
        self.show_images(
            images=image_data,
            scrollable_frame=self.local_scrollable_frame,
            canvas=self.local_canvas,
            on_click=lambda info: self.set_wallpaper(info["path"])
        )

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
            self.local_image_manager.set_folder(folder)
            self.config["last_folder"] = folder
            ConfigManager.save_config(self.config)
            self.current_page.set(0)
            self.display_images()

    def open_settings(self):
        settings_ui = SettingsUI(self.root, self.config, self.current_language, self)
        settings_ui.open_settings_window()

    def github_login(self):
        """触发 GitHub 登录流程"""
        if self.user_info:
            self.status_var.set(f"欢迎回来, 用户名: {self.user_info['username']}")
            self.oss_ui_handler.update_uid(self.user_info["id"])
            self.update_to_avatar_button()  # 切换为头像按钮
            return

        self.status_var.set("正在登录，请完成 GitHub 授权...")

        try:
            user_info = self.github_auth.login()
            self.user_info = user_info
            self.status_var.set(f"登录成功，用户名: {user_info['username']}")
            self.user_info_manager.save_user_info(user_info)
            self.update_to_avatar_button()  # 切换为头像按钮
            print("用户信息已保存")
            self.oss_ui_handler.update_uid(user_info["id"])
        except Exception as e:
            self.status_var.set(f"登录失败: {e}")

    def logout(self):
        """退出登录"""
        self.user_info_manager.clear_user_info()  # 清空本地缓存
        self.user_info = None
        self.update_to_login_button()  # 切换为登录按钮
        self.status_var.set(LanguageManager.get_text(self.current_language.get(), "ready"))


    def save_user_info(self, user_info):
        """保存用户信息到本地文件"""
        with open("user_info.json", "w") as file:
            json.dump(user_info, file)

        print("用户信息已保存到本地")

    def update_ui_texts(self):
        # 更新状态栏
        self.status_var.set(LanguageManager.get_text(self.current_language.get(), "ready"))

        # 更新顶部按钮
        self.top_buttons[0].config(text=LanguageManager.get_text(self.current_language.get(), "wallpaper_folder"))
        self.top_buttons[1].config(text=LanguageManager.get_text(self.current_language.get(), "select_folder"))
        self.top_buttons[2].config(text=LanguageManager.get_text(self.current_language.get(), "settings"))

        # 更新分页按钮
        self.local_image_manager.update_ui_texts(self.current_language)
        self.oss_ui_handler.update_ui_texts(self.current_language)

        # 更新登录按钮文本
        if self.login_button.winfo_ismapped():  # 如果登录按钮当前可见
            self.login_button.config(text=LanguageManager.get_text(self.current_language.get(), "login"))

        # 更新头像菜单文本
        if self.avatar_menu:
            self.avatar_menu.entryconfig(0, label=LanguageManager.get_text(self.current_language.get(), "logout"))

        # 更新 Tab 标签
        self.notebook.tab(0, text=LanguageManager.get_text(self.current_language.get(), "local_wallpapers"))
        self.notebook.tab(1, text=LanguageManager.get_text(self.current_language.get(), "oss_wallpapers"))

    def on_canvas_resize(self, event):
        """窗口大小变化时更新布局"""
        self.display_local_images()

    def save_user_id(self, user_id):
        """保存用户 ID 到本地"""
        with open("user_id.txt", "w") as file:
            file.write(str(user_id))