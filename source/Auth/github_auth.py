import http.server
import threading
import webbrowser
import json
from urllib.parse import unquote


class GitHubAuth:
    """GitHub 登录逻辑"""

    CALLBACK_PORT = 8000
    LOGIN_URL = "http://39.96.125.57:5000/login/github"  # 服务端登录 URL

    def __init__(self):
        self.user_info = None  # 存储用户信息

    class LocalCallbackHandler(http.server.BaseHTTPRequestHandler):
        """本地 HTTP 服务用于接收服务端返回的用户信息"""

        def do_GET(self):
            path = self.path
            print(f"Callback Path: {self.path}")
            if "user_info=" in path:
                # 解码 URL 参数
                encoded_user_info = path.split("user_info=")[-1]
                user_info_json = unquote(encoded_user_info)
                user_info = json.loads(user_info_json)
                print(f"Received User Info: {user_info}")
                self.server.user_info = user_info
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Login Successful! You can close this window.")
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid Request: Missing user info.")

    def start_callback_server(self):
        """启动本地 HTTP 服务器监听回调"""
        server = http.server.HTTPServer(("localhost", self.CALLBACK_PORT), self.LocalCallbackHandler)
        server.user_info = None
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server

    def login(self):
        """执行 GitHub 登录流程"""
        # 启动本地服务器监听回调
        local_server = self.start_callback_server()

        # 打开 GitHub 登录页面
        webbrowser.open(self.LOGIN_URL)

        # 等待服务端返回用户信息
        print("Waiting for GitHub login to complete...")
        while not local_server.user_info:
            pass  # 阻塞等待用户信息

        self.user_info = local_server.user_info
        return self.user_info
