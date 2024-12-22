import pickle
from cryptography.fernet import Fernet

class UserInfoManager:
    USER_INFO_FILE = "user_info.dat"
    ENCRYPTION_KEY_FILE = "encryption_key.dat"

    def __init__(self):
        self.cipher = self._load_or_generate_key()

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

    def save_user_info(self, user_info):
        """加密并保存用户信息"""
        try:
            encrypted_data = self.cipher.encrypt(pickle.dumps(user_info))
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
            user_info = pickle.loads(self.cipher.decrypt(encrypted_data))
            print("用户信息已加载并解密")
            return user_info
        except FileNotFoundError:
            print("用户信息文件不存在")
            return None
        except Exception as e:
            print(f"加载用户信息时出错: {e}")
            return None
