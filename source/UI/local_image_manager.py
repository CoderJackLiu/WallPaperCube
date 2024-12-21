# local_image_manager.py
import os
import math
from tkinter import Button, Label, Frame
from source.image_manager import ImageManager
from source.language_manager import LanguageManager


class LocalImageManager:
    def __init__(self, current_language=None, images_per_page=24):
        self.images_per_page = images_per_page
        self.current_page = 0
        self.folder_path = ""
        self.current_language = current_language

    def set_folder(self, folder_path):
        """设置图片文件夹路径并重置分页"""
        self.folder_path = folder_path
        self.current_page = 0

    def get_total_pages(self):
        """计算总页数"""
        total_images = len(self._get_images())
        return math.ceil(total_images / self.images_per_page)

    def get_current_page_images(self):
        """获取当前页的图片路径"""
        images = self._get_images()
        start_index = self.current_page * self.images_per_page
        end_index = min(start_index + self.images_per_page, len(images))
        return images[start_index:end_index]

    def _get_images(self):
        """获取文件夹中的所有图片"""
        if not self.folder_path:
            return []
        return ImageManager.get_images_in_folder(self.folder_path)

    def get_image_data(self):
        """获取当前页的图片数据（包括缩略图和路径）"""
        images = self.get_current_page_images()
        image_data = []
        for image_path in images:
            thumbnail = ImageManager.generate_thumbnail(image_path)
            if thumbnail:
                image_data.append({
                    "thumbnail": thumbnail,
                    "text": os.path.basename(image_path),
                    "path": image_path
                })
        return image_data

    def get_pagination_ui(self, parent_frame, update_callback):
        """生成分页按钮并返回容器"""
        pagination_frame = Frame(parent_frame)

        # 创建上一页按钮
        self.previous_button = Button(
            pagination_frame, text=LanguageManager.get_text(self.current_language.get(), "previous"),
            command=lambda: self.previous_page_and_update(update_callback)
        )

        # 创建页码标签
        self.page_label = Label(
            pagination_frame,
            text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page + 1)
        )

        # 创建下一页按钮
        self.next_button = Button(
            pagination_frame, text=LanguageManager.get_text(self.current_language.get(), "next"),
            command=lambda: self.next_page_and_update(update_callback)
        )

        # 布局按钮和页码标签
        self.previous_button.grid(row=0, column=0, padx=10)
        self.page_label.grid(row=0, column=1, padx=0)
        self.next_button.grid(row=0, column=2, padx=10)

        # 在父容器中居中显示分页框
        pagination_frame.pack(anchor="center", pady=10)

        # 返回分页框和页码标签
        return pagination_frame, self.page_label

    def previous_page_and_update(self, update_callback):
        """切换到上一页并更新显示"""
        if self.current_page > 0:
            self.current_page -= 1
            # 动态获取多语言的页码文本
            self.page_label.config(
                text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page + 1)
            )
            update_callback()

    def next_page_and_update(self, update_callback):
        """切换到下一页并更新显示"""
        if self.current_page < self.get_total_pages() - 1:
            self.current_page += 1
            # 动态获取多语言的页码文本
            self.page_label.config(
                text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page + 1)
            )
            update_callback()

    def update_ui_texts(self,current_language):
        self.current_language = current_language
        self.page_label.config(
            text=LanguageManager.get_text(self.current_language.get(), "page", page=self.current_page + 1)
        )
        # 更新self.previous_button的文本
        self.previous_button.config(
            text=LanguageManager.get_text(self.current_language.get(), "previous")
        )
        # 更新self.next_button的文本
        self.next_button.config(
            text=LanguageManager.get_text(self.current_language.get(), "next")
        )