import oss2


class AliyunOSS:
    def __init__(self, access_key_id, access_key_secret, endpoint, bucket_name):
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)

    def list_wallpapers(self, prefix=""):
        """
        列出指定前缀的壁纸文件。
        :param prefix: 文件前缀
        :return: 文件列表
        """
        wallpapers = []
        for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
            if obj.key.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                wallpapers.append(obj.key)
        return wallpapers

    def download_wallpaper(self, remote_file, local_path):
        """
        下载指定文件到本地。
        :param remote_file: OSS 上的文件名
        :param local_path: 下载到的本地路径
        """
        self.bucket.get_object_to_file(remote_file, local_path)
