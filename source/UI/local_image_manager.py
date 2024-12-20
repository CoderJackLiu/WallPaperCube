# local_image_manager.py
import os
import math
from tkinter import Button, Label, Frame

from PIL import Image, ImageTk
from source.image_manager import ImageManager

class LocalImageManager:
    def __init__(self, images_per_page=24):
        self.images_per_page = images_per_page
        self.current_page = 0
        self.folder_path = ""

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

    def next_page(self):
        """切换到下一页"""
        if self.current_page < self.get_total_pages() - 1:
            self.current_page += 1

    def previous_page(self):
        """切换到上一页"""
        if self.current_page > 0:
            self.current_page -= 1

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

        # 布局按钮和页码标签
        previous_button.grid(row=0, column=0, padx=10)
        page_label.grid(row=0, column=1, padx=0)
        next_button.grid(row=0, column=2, padx=10)

        # 在父容器中居中显示分页框
        pagination_frame.pack(anchor="center", pady=10)

        # 返回分页框和页码标签
        return pagination_frame, page_label

    def previous_page_and_update(self, update_callback):
        """切换到上一页并更新显示"""
        if self.current_page > 0:
            self.current_page -= 1
            update_callback()

    def next_page_and_update(self, update_callback):
        """切换到下一页并更新显示"""
        if self.current_page < self.get_total_pages() - 1:
            self.current_page += 1
            update_callback()