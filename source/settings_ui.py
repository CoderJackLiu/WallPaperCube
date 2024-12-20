from tkinter import Toplevel, Frame, Label, Button, IntVar, StringVar, ttk, Entry, Checkbutton
from config_manager import ConfigManager
from cloud_services.oss_config import OSSConfig
from language_manager import LanguageManager

class SettingsUI:
    def __init__(self, root, config, current_language, app_ui_instance):
        self.root = root
        self.config = config
        self.current_language = current_language
        self.app_ui_instance = app_ui_instance  # 直接传递 AppUI 实例

        # 保存通用配置
        self.auto_switch_var = IntVar(value=config.get("auto_switch_enabled", 0))
        self.interval_var = IntVar(value=config.get("auto_switch_interval", 5))
        self.language_var = StringVar(value=current_language.get())

        # 保存 OSS 配置
        self.oss_config = OSSConfig.load_config()
        self.oss_enabled_var = IntVar(value=self.oss_config.get("oss_enabled", 0))
        self.access_key_var = StringVar(value=self.oss_config.get("oss_access_key_id", ""))
        self.secret_key_var = StringVar(value=self.oss_config.get("oss_access_key_secret", ""))
        self.endpoint_var = StringVar(value=self.oss_config.get("oss_endpoint", ""))
        self.bucket_var = StringVar(value=self.oss_config.get("oss_bucket_name", ""))

    def open_settings_window(self):
        settings_window = Toplevel(self.root)
        settings_window.title(LanguageManager.get_text(self.current_language.get(), "settings"))
        settings_window.grab_set()
        settings_window.transient(self.root)

        # 窗口居中定位
        settings_width, settings_height = 500, 400
        x_position = self.root.winfo_x() + (self.root.winfo_width() // 2) - (settings_width // 2)
        y_position = self.root.winfo_y() + (self.root.winfo_height() // 2) - (settings_height // 2)
        settings_window.geometry(f"{settings_width}x{settings_height}+{x_position}+{y_position}")

        # 创建 Notebook（侧边栏选项卡）
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 添加选项卡
        general_frame = self._create_general_settings(notebook)
        oss_frame = self._create_oss_settings(notebook)

        notebook.add(general_frame, text=LanguageManager.get_text(self.current_language.get(), "general_settings"))
        notebook.add(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "oss_settings"))

        # 保存按钮
        Button(settings_window, text=LanguageManager.get_text(self.current_language.get(), "save_settings"), command=lambda: self._save_settings(settings_window)).pack(pady=10)

    def _create_general_settings(self, notebook):
        general_frame = Frame(notebook)
        Label(general_frame, text=LanguageManager.get_text(self.current_language.get(), "select_language")).pack(pady=5)
        language_combobox = ttk.Combobox(general_frame, values=["English", "Chinese"], state="readonly")
        language_combobox.set(self.language_var.get())
        language_combobox.pack(pady=5)
        self.language_combobox = language_combobox

        Checkbutton(general_frame, text=LanguageManager.get_text(self.current_language.get(), "enable_auto_switch"), variable=self.auto_switch_var).pack(pady=5)
        Label(general_frame, text=LanguageManager.get_text(self.current_language.get(), "auto_switch_interval")).pack(pady=5)
        interval_entry = ttk.Spinbox(general_frame, from_=5, to=600, textvariable=self.interval_var, state="readonly")
        interval_entry.pack(pady=5)
        return general_frame

    def _create_oss_settings(self, notebook):
        oss_frame = Frame(notebook)
        Checkbutton(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "enable_oss"), variable=self.oss_enabled_var).pack(pady=5)
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "access_key_id")).pack(pady=5)
        Entry(oss_frame, textvariable=self.access_key_var).pack(pady=5)
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "access_key_secret")).pack(pady=5)
        Entry(oss_frame, textvariable=self.secret_key_var, show="*").pack(pady=5)
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "endpoint")).pack(pady=5)
        Entry(oss_frame, textvariable=self.endpoint_var).pack(pady=5)
        Label(oss_frame, text=LanguageManager.get_text(self.current_language.get(), "bucket_name")).pack(pady=5)
        Entry(oss_frame, textvariable=self.bucket_var).pack(pady=5)
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
            self.app_ui_instance.start_auto_switch(self.interval_var.get())
        else:
            self.app_ui_instance.stop_auto_switch()

        # 更新 UI 文本
        self.app_ui_instance.update_ui_texts()

        # 关闭设置窗口
        settings_window.destroy()

