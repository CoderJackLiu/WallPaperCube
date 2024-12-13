### image_manager.py
import os
from PIL import Image, ImageTk
import hashlib

THUMBNAIL_DIR = "thumbnails"

class ImageManager:
    @staticmethod
    def get_images_in_folder(folder_path):
        try:
            return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]
        except Exception as e:
            print(f"Error: {e}")
            return []

    @staticmethod
    def generate_thumbnail(image_path):
        if not os.path.exists(THUMBNAIL_DIR):
            os.makedirs(THUMBNAIL_DIR)

        file_stat = os.stat(image_path)
        unique_id = f"{image_path}-{file_stat.st_mtime}".encode('utf-8')
        hashed_id = hashlib.md5(unique_id).hexdigest()
        thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{hashed_id}_thumbnail.png")

        try:
            if os.path.exists(thumbnail_path):
                with Image.open(thumbnail_path) as cached_img:
                    return ImageTk.PhotoImage(cached_img)

            # 如果缓存不存在，生成新缩略图
            with Image.open(image_path) as img:
                img.thumbnail((100, 100))
                img.save(thumbnail_path)
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error generating thumbnail for {image_path}: {e}")
            return None
