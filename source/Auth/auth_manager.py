import requests
from tkinter import Toplevel, Label, Entry, Button, StringVar, messagebox, Frame
from Auth.github_auth import GitHubAuth


class AuthManager:
    def __init__(self, root, status_var, user_info_manager, uiInstance):
        self.root = root
        self.status_var = status_var
        self.user_info_manager = user_info_manager
        self.github_auther = GitHubAuth()  # 初始化 GitHub 鉴权模块
        self.user_info = self.user_info_manager.load_user_info()
        self.is_registration = False  # 是否处于注册模式
        self.remote_server_url = "http://39.96.125.57:5000"  # 服务端登录 URL
        self.uiInstance = uiInstance;

    def open_login_window(self):
        """打开登录窗口"""
        self.login_window = Toplevel(self.root)
        self.login_window.title("登录")
        self.login_window.geometry("400x300")
        self.login_window.transient(self.root)  # 设置为模态窗口
        self.login_window.grab_set()  # 阻止主窗口交互
        self.login_window.resizable(False, False)

        # 窗口居中
        window_width, window_height = 400, 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_cordinate = int((screen_width / 2) - (window_width / 2))
        y_cordinate = int((screen_height / 2) - (window_height / 2))
        self.login_window.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

        # 动态变量
        email_var = StringVar()
        password_var = StringVar()
        code_var = StringVar()

        def send_verification_code():
            """通过服务端发送验证码"""
            email = email_var.get()
            if not email:
                messagebox.showerror("错误", "请输入邮箱地址")
                return

            try:

                response = requests.post(f"{self.remote_server_url}/send_verification_code", json={"email": email})
                if response.status_code == 200:
                    messagebox.showinfo("提示", "验证码已发送到您的邮箱，请查收！")
                else:
                    messagebox.showerror("错误", response.json().get("error", "发送验证码失败"))
            except Exception as e:
                messagebox.showerror("错误", f"无法连接服务器: {e}")

        def handle_login():
            """通过服务端登录"""
            email = email_var.get()
            password = password_var.get()
            if not email or not password:
                messagebox.showerror("错误", "请输入邮箱和密码")
                return

            try:
                response = requests.post(f"{self.remote_server_url}/login", json={"email": email, "password": password})
                if response.status_code == 200:
                    user_info = response.json()["user_info"]
                    self.user_info_manager.save_user_info(user_info["email"], user_info["id"])
                    self.status_var.set(f"登录成功，邮箱: {email}")
                    self.update_to_avatar_button()  # 更新主面板按钮
                    self.login_window.destroy()
                else:
                    messagebox.showerror("错误", response.json().get("error", "登录失败"))
            except Exception as e:
                messagebox.showerror("错误", f"无法连接服务器: {e}")

        def handle_registration():
            """通过服务端注册"""
            email = email_var.get()
            code = code_var.get()
            password = password_var.get()
            if not email or not code or not password:
                messagebox.showerror("错误", "请填写完整信息")
                return

            try:
                response = requests.post(
                    f"{self.remote_server_url}/register",
                    json={"email": email, "password": password, "verification_code": code},
                )
                if response.status_code == 201:
                    self.status_var.set(f"注册成功并登录，邮箱: {email}")
                    self.update_to_avatar_button()  # 更新主面板按钮
                    self.login_window.destroy()
                else:
                    messagebox.showerror("错误", response.json().get("error", "注册失败"))
            except Exception as e:
                messagebox.showerror("错误", f"无法连接服务器: {e}")

        def switch_to_register():
            """切换到注册界面"""
            self.is_registration = True
            render_ui()

        def switch_to_login():
            """切换到登录界面"""
            self.is_registration = False
            render_ui()

        def render_ui():
            """渲染登录或注册界面"""
            for widget in self.login_window.winfo_children():
                widget.destroy()

            frame = Frame(self.login_window)
            frame.pack(expand=True)

            if self.is_registration:
                # 注册界面
                Label(frame, text="邮箱:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
                Entry(frame, textvariable=email_var).grid(row=0, column=1, padx=10, pady=10, sticky="w")

                Label(frame, text="验证码:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
                Entry(frame, textvariable=code_var).grid(row=1, column=1, padx=10, pady=10, sticky="w")
                Button(frame, text="发送验证码", command=send_verification_code).grid(row=1, column=2, padx=10, pady=10)

                Label(frame, text="密码:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
                Entry(frame, textvariable=password_var, show="*").grid(row=2, column=1, padx=10, pady=10, sticky="w")

                Button(frame, text="注册", command=handle_registration).grid(row=3, column=0, padx=5, pady=10)
                Button(frame, text="返回登录", command=switch_to_login).grid(row=3, column=1, padx=5, pady=10)
            else:
                # 登录界面
                Label(frame, text="邮箱:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
                Entry(frame, textvariable=email_var).grid(row=0, column=1, padx=10, pady=10, sticky="w")

                Label(frame, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
                Entry(frame, textvariable=password_var, show="*").grid(row=1, column=1, padx=10, pady=10, sticky="w")

                Button(frame, text="登录", command=handle_login).grid(row=2, column=0, padx=5, pady=10)
                Button(frame, text="注册", command=switch_to_register).grid(row=2, column=1, padx=5, pady=10)

            # GitHub 快速登录按钮
            Button(frame, text="GitHub 快速登录", command=self.github_login).grid(row=4, column=0, columnspan=3,
                                                                                  pady=10)

        render_ui()

    def github_login(self):
        """GitHub 登录逻辑"""
        try:
            user_info = self.github_auther.login()
            self.user_info = user_info
            self.status_var.set(f"GitHub 登录成功，用户名: {user_info['username']}")
            self.user_info_manager.save_user_info(user_info['email'], user_info['id'])
            self.update_to_avatar_button()  # 更新主面板按钮
            self.login_window.destroy()
        except Exception as e:
            messagebox.showerror("登录失败", f"GitHub 登录失败: {e}")

    def update_to_avatar_button(self):
        """更新主面板登录按钮为头像或默认按钮"""
        self.status_var.set("切换到头像按钮")
        self.uiInstance.update_to_avatar_button()
