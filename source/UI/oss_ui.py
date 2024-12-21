import math
import os
from tkinter import Frame, Label, Canvas, Scrollbar, Button
from source.language_manager import LanguageManager

class OSSUIHandler:
    def __init__(self, root, oss, status_var, current_language, uiInstance):
        self.oss_images = None
        self.root = root
        self.oss = oss
        self.uiInstance = uiInstance
        self.status_var = status_var
        self.current_language = current_language
        self.oss_canvas = None
        self.oss_scrollable_frame = None
        self.current_page = 0

    def get_total_pages(self):
        """计算 OSS 壁纸的总页数"""
        if not hasattr(self, 'oss_images') or not self.oss_images:
            return 1  # 如果没有加载图片，返回默认总页数为 1

        total_images = len(self.oss_images)  # 假设 oss_images 包含所有壁纸数据
        return math.ceil(total_images / self.uiInstance.images_per_page)

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
            self.uiInstance.set_wallpaper(local_path)

            # 更新缓存标记
            self.root.after(0, self._add_cached_mark, file_name)

            # 调试信息
            print(f"Downloaded and marked: {file_name}")

            # 更新状态栏
            msgInfo = LanguageManager.get_text(self.current_language.get(), "wallpaper_set_to", wallpaper={file_name})

            print(f"msgInfo msgInfo msgInfo: {msgInfo}")
            # self.uiInstance.status_var.set(msgInfo)
            # self.uiInstance.status_var.set(f"Wallpaper set: {local_path}")
        except Exception as e:
            self.uiInstance.status_var.set(f"Failed to download or set wallpaper: {e}")

    def display_oss_images(self, wallpapers=None):
        """显示 OSS 壁纸"""
        if not self.oss.enabled:
            self.uiInstance.status_var.set(LanguageManager.get_text(self.current_language, "oss_not_configured"))
            return

        if wallpapers is None:
            try:
                wallpapers = self.oss.list_wallpapers(prefix="wallpapers/")
                self.oss_images = wallpapers  # 初始化 oss_images
                for wallpaper in wallpapers:
                    local_file_name = wallpaper["original"].split("/")[-1]
                    local_path = os.path.abspath(f"downloads/{local_file_name}")
                    wallpaper["is_cached"] = os.path.exists(local_path)
            except Exception as e:
                error_message = LanguageManager.get_text(self.current_language, "oss_load_failed", error=str(e))
                self.uiInstance.status_var.set(error_message)
                return

        # 准备图片数据
        image_data = []
        for wallpaper in wallpapers:
            thumbnail = self.oss.fetch_thumbnail(wallpaper["thumbnail"])
            if thumbnail:
                image_data.append({
                    "thumbnail": thumbnail,
                    "text": wallpaper["original"].split("/")[-1],
                    "path": wallpaper["original"],
                    "is_cached": wallpaper.get("is_cached", False)
                })

        # 调用 show_images
        self.uiInstance.show_images(
            images=image_data,
            scrollable_frame=self.uiInstance.oss_scrollable_frame,
            canvas=self.uiInstance.oss_canvas,
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

    def get_pagination_ui(self, parent_frame, update_callback):
        """生成分页按钮并返回容器"""
        pagination_frame = Frame(parent_frame)

        # 创建上一页按钮
        previous_button = Button(
            pagination_frame, text="Previous",
            command=lambda: self.previous_page_and_update(update_callback)
        )

        # 创建页码标签
        page_label = Label(
            pagination_frame, text=f"Page {self.current_page + 1}"
        )

        # 创建下一页按钮
        next_button = Button(
            pagination_frame, text="Next",
            command=lambda: self.next_page_and_update(update_callback)
        )

        # 使用 grid 布局居中
        previous_button.grid(row=0, column=0, padx=10)
        page_label.grid(row=0, column=1, padx=0)
        next_button.grid(row=0, column=2, padx=10)

        # 在父容器中居中显示分页框
        pagination_frame.pack(anchor="center", pady=10)

        return pagination_frame, page_label

    def next_page_and_update(self, update_callback):
        """切换到下一页并更新显示"""
        if self.current_page < self.get_total_pages() - 1:
            self.current_page += 1
            update_callback()

    def previous_page_and_update(self, update_callback):
        """切换到上一页并更新显示"""
        if self.current_page > 0:
            self.current_page -= 1
            update_callback()

    def on_canvas_resize(self, event):
        """窗口大小变化时更新布局"""
        self.display_oss_images()

    def update_ui_texts(self, current_language):
        pass