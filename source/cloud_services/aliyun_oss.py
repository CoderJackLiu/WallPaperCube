import hashlib
import io
import os
import ssl
from urllib.request import urlopen

import oss2
from PIL import ImageTk, Image

OSS_WALLPAPER_DIR = "downloads"

class AliyunOSS:
    def __init__(self, access_key_id, access_key_secret, endpoint, bucket_name):
        if not all([access_key_id, access_key_secret, endpoint, bucket_name]):
            print("OSS configuration is incomplete. OSS functionality is disabled.")
            self.enabled = False
            return

        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
        self.enabled = True  # 标记 OSS 功能已启用

    def list_wallpapers(self, prefix=""):
        if not self.enabled:
            raise ValueError("OSS functionality is disabled due to incomplete configuration.")
        wallpapers = []
        endpoint_url = self.bucket.endpoint.replace("http://", "").replace("https://", "")  # 确保只包含纯域名
        for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
            if obj.key.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                thumbnail_url = f"https://{self.bucket.bucket_name}.{endpoint_url}/{obj.key}?x-oss-process=image/resize,w_100"
                wallpapers.append({"original": obj.key, "thumbnail": thumbnail_url})
        return wallpapers

    def download_wallpaper(self, remote_file, local_path):
        if not self.enabled:
            raise ValueError("OSS functionality is disabled due to incomplete configuration.")

        if not os.path.exists(OSS_WALLPAPER_DIR):
            os.makedirs(OSS_WALLPAPER_DIR)
        self.bucket.get_object_to_file(remote_file, local_path)

    def fetch_thumbnail(self, thumbnail_url):
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