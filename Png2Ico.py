from PIL import Image

# 加载 PNG 图片
png_file = "icon.png"  # 替换为您的 PNG 图片路径
ico_file = "icon.ico"  # 替换为目标 ICO 文件路径

# 打开图片并转换为 ICO
image = Image.open(png_file)
image.save(ico_file, format="ICO", sizes=[(256, 256)])

print("PNG 已成功转换为 ICO 文件！")
