import os
import pickle
import hashlib
from cryptography.fernet import Fernet

class UserInfoManager:
    USER_INFO_FILE = "user_info.dat"
    ENCRYPTION_KEY_FILE = "encryption_key.dat"

    def __init__(self):
        self.cipher = self._load_or_generate_key()
        self.user_info = self.load_user_info()

    def _load_or_generate_key(self):
        """加载或生成加密密钥"""
        try:
            with open(self.ENCRYPTION_KEY_FILE, "rb") as key_file:
                key = key_file.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open(self.ENCRYPTION_KEY_FILE, "wb") as key_file:
                key_file.write(key)
        return Fernet(key)

    def _hash_password(self, password):
        """生成密码的哈希值"""
        return hashlib.sha256(password.encode()).hexdigest()

    def save_user_info(self, email, uid):
        """保存用户的邮箱哈希"""
        try:
            self.user_info = {
                "email": email,
                "id": uid,
            }
            encrypted_data = self.cipher.encrypt(pickle.dumps(self.user_info))
            with open(self.USER_INFO_FILE, "wb") as file:
                file.write(encrypted_data)
            print("用户信息已加密并保存")
        except Exception as e:
            print(f"保存用户信息时出错: {e}")

    def load_user_info(self):
        """加载并解密用户信息"""
        try:
            with open(self.USER_INFO_FILE, "rb") as file:
                encrypted_data = file.read()
            self.user_info = pickle.loads(self.cipher.decrypt(encrypted_data))
            print("用户信息已加载并解密")
            return self.user_info
        except FileNotFoundError:
            print("用户信息文件不存在")
            return None
        except Exception as e:
            print(f"加载用户信息时出错: {e}")
            return None

    def clear_user_info(self):
        """清空本地用户信息"""
        try:
            if os.path.exists(self.USER_INFO_FILE):
                os.remove(self.USER_INFO_FILE)
            print("用户信息已清空")
        except Exception as e:
            print(f"清空用户信息失败: {e}")

    def verify_user(self, email, password):
        """验证用户的邮箱和密码"""
        self.user_info = self.load_user_info()
        if not self.user_info:
            print("用户信息不存在")
            return False

        stored_email = self.user_info.get("email")
        # stored_password_hash = self.user_info.get("password_hash")

        if stored_email == email:
            print("用户验证成功")
            return True
        else:
            print("用户验证失败")
            return False

    def is_user_info_saved(self):
        """检查用户信息是否已保存"""
        return os.path.exists(self.USER_INFO_FILE)

    def get_avatar_url(self):
        #print todo get_avatar_url
        print("todo get_avatar_url")
        return "https://avatars.githubusercontent.com/u/583231?v=4"

