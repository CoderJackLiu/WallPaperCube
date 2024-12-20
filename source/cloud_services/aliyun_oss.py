import os

import oss2

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
