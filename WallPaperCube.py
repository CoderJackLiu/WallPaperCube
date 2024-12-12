import os
import ctypes
import json
import threading
from tkinter import Tk, filedialog, Label, Button, Frame, StringVar, Canvas, Scrollbar
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
import hashlib
import tkinter as tk
import math

# Config file for storing folder path and language
CONFIG_FILE = "config.json"
THUMBNAIL_DIR = "thumbnails"
DEFAULT_FOLDER = os.path.expanduser("~/Pictures")

# Language dictionary
LANGUAGES = {
    "English": {
        "select_folder": "Select Folder",
        "settings": "Settings",
        "wallpaper_folder": "Wallpaper Folder:",
        "previous": "Previous",
        "next": "Next",
        "page": "Page {page}",
        "ready": "Ready",
        "wallpaper_set_to": "Wallpaper set to: {wallpaper}",
        "wallpaper_failed": "Failed to set wallpaper: {error}",
    },
    "Chinese": {
        "select_folder": "\u9009\u62e9\u6587\u4ef6\u5939",
        "settings": "\u8bbe\u7f6e",
        "wallpaper_folder": "\u58c1\u7eb8\u6587\u4ef6\u5939\uff1a",
        "previous": "\u4e0a\u4e00\u9875",
        "next": "\u4e0b\u4e00\u9875",
        "page": "\u7b2c{page}\u9875",
        "ready": "\u51c6\u5907\u5b8c\u6210",
        "wallpaper_set_to": "\u58c1\u7eb8\u5df2\u8bbe\u7f6e\u4e3a\uff1a{wallpaper}",
        "wallpaper_failed": "\u8bbe\u7f6e\u58c1\u7eb8\u5931\u8d25\uff1a{error}",
    },
}

current_language = None  # Initialize after root creation

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            try:
                config = json.load(file)
                if not config.get("last_folder"):
                    raise ValueError("Config missing 'last_folder'")
                return config
            except Exception as e:
                print(f"Error loading config: {e}")
    return {"last_folder": DEFAULT_FOLDER, "language": "English"}

def update_ui_texts():
    """Update the UI texts based on the selected language."""
    lang = current_language.get()
    top_label.config(text=LANGUAGES[lang]["wallpaper_folder"])
    select_button.config(text=LANGUAGES[lang]["select_folder"])
    settings_button.config(text=LANGUAGES[lang]["settings"])
    prev_button.config(text=LANGUAGES[lang]["previous"])
    next_button.config(text=LANGUAGES[lang]["next"])
    status_var.set(LANGUAGES[lang]["ready"])
    page_label.config(text=LANGUAGES[lang]['page'].format(page=current_page.get() + 1))

def open_settings():
    """Open the settings panel."""
    settings_window = tk.Toplevel(root)
    settings_window.title(LANGUAGES[current_language.get()]['settings'])

    # Center the settings window
    settings_width, settings_height = 300, 150
    settings_x = (root.winfo_x() + root.winfo_width() // 2) - (settings_width // 2)
    settings_y = (root.winfo_y() + root.winfo_height() // 2) - (settings_height // 2)
    settings_window.geometry(f"{settings_width}x{settings_height}+{settings_x}+{settings_y}")

    settings_window.transient(root)  # Set window on top of root
    settings_window.grab_set()  # Make it modal

    Label(settings_window, text="Select Language:").pack(pady=10)
    language_combobox = ttk.Combobox(
        settings_window, values=list(LANGUAGES.keys()), state="readonly"
    )
    language_combobox.set(current_language.get())
    language_combobox.pack(pady=10)

    def save_settings():
        selected_language = language_combobox.get()
        current_language.set(selected_language)
        config["language"] = selected_language
        save_config(config)
        update_ui_texts()
        display_images(folder_path.get(), scrollable_frame, current_page, images_per_page, status_var, canvas.winfo_width())
        settings_window.destroy()

    Button(settings_window, text="Save", command=save_settings).pack(pady=10)

def set_wallpaper(image_path, status_var):
    SPI_SETDESKWALLPAPER = 20
    lang = current_language.get()
    try:
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
        status_var.set(LANGUAGES[lang]["wallpaper_set_to"].format(wallpaper=os.path.basename(image_path)))
    except Exception as e:
        status_var.set(LANGUAGES[lang]["wallpaper_failed"].format(error=str(e)))

def get_images_in_folder(folder_path):
    try:
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp"))]
    except Exception as e:
        print(f"Error: {e}")
        return []

def generate_thumbnail(image_path):
    if not os.path.exists(THUMBNAIL_DIR):
        os.makedirs(THUMBNAIL_DIR)

    file_stat = os.stat(image_path)
    unique_id = f"{image_path}-{file_stat.st_mtime}".encode('utf-8')
    hashed_id = hashlib.md5(unique_id).hexdigest()
    thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{hashed_id}_thumbnail.png")

    if os.path.exists(thumbnail_path):
        try:
            with Image.open(thumbnail_path) as cached_img:
                return ImageTk.PhotoImage(cached_img)
        except Exception as e:
            print(f"Failed to load cached thumbnail for {image_path}: {e}")

    try:
        with Image.open(image_path) as img:
            img.thumbnail((100, 100))
            img.save(thumbnail_path)
            return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Failed to create thumbnail for {image_path}: {e}")
        return None

def display_images(folder, scrollable_frame, current_page, images_per_page, status_var, canvas_width):
    images = get_images_in_folder(folder)
    total_images = len(images)
    max_page = math.ceil(total_images / images_per_page) - 1

    if current_page.get() > max_page:
        current_page.set(max_page)

    start_index = current_page.get() * images_per_page
    end_index = min(start_index + images_per_page, total_images)
    loaded_images = [(image_path, generate_thumbnail(image_path)) for image_path in images[start_index:end_index]]

    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    columns = max(canvas_width // 120, 1)

    for index, (image_path, thumbnail) in enumerate(loaded_images):
        img_label = Label(scrollable_frame, image=thumbnail, text=Path(image_path).name, compound="top", bg="white")
        img_label.photo = thumbnail
        img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)
        img_label.bind("<Button-1>", lambda event, path=image_path: set_wallpaper(path, status_var))

    # Update the page label dynamically
    page_label.config(text=LANGUAGES[current_language.get()]['page'].format(page=current_page.get() + 1))

def on_canvas_resize(event):
    display_images(folder_path.get(), scrollable_frame, current_page, images_per_page, status_var, event.width)

# GUI Application
root = Tk()
root.title("Wallpaper Changer")

config = load_config()

current_language = StringVar(root, value=config.get("language", "English"))  # Initialize after root creation

window_width, window_height = 800, 600
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = (screen_height // 2) - (window_height // 2)
position_right = (screen_width // 2) - (window_width // 2)
root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

folder_path = StringVar(root, value=config.get("last_folder", DEFAULT_FOLDER))
status_var = StringVar(root, value=LANGUAGES[current_language.get()]["ready"])
current_page = tk.IntVar(root, value=0)
images_per_page = 24

def select_folder():
    folder = filedialog.askdirectory(title=LANGUAGES[current_language.get()]["select_folder"])
    if folder:
        folder_path.set(folder)
        config["last_folder"] = folder
        save_config(config)
        display_images(folder, scrollable_frame, current_page, images_per_page, status_var, canvas.winfo_width())

# UI Layout
top_frame = Frame(root)
top_frame.pack(fill="x", padx=10, pady=5)

top_label = Label(top_frame, text=LANGUAGES[current_language.get()]["wallpaper_folder"])
top_label.pack(side="left")

select_button = Button(top_frame, text=LANGUAGES[current_language.get()]["select_folder"], command=select_folder)
select_button.pack(side="left")

settings_button = Button(top_frame, text=LANGUAGES[current_language.get()]["settings"], command=open_settings)
settings_button.pack(side="right")

canvas_frame = Frame(root)
canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)

canvas = Canvas(canvas_frame)
scrollbar = Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
scrollable_frame = Frame(canvas)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

canvas.bind("<Configure>", on_canvas_resize)

def next_page():
    if folder_path.get():
        images = get_images_in_folder(folder_path.get())
        max_page = math.ceil(len(images) / images_per_page) - 1
        if current_page.get() < max_page:
            current_page.set(current_page.get() + 1)
            display_images(folder_path.get(), scrollable_frame, current_page, images_per_page, status_var, canvas.winfo_width())

def previous_page():
    if folder_path.get() and current_page.get() > 0:
        current_page.set(current_page.get() - 1)
        display_images(folder_path.get(), scrollable_frame, current_page, images_per_page, status_var, canvas.winfo_width())

pagination_frame = Frame(root)
pagination_frame.pack(fill="x", padx=10, pady=5)

pagination_inner_frame = Frame(pagination_frame)
pagination_inner_frame.pack(anchor="center")

prev_button = Button(pagination_inner_frame, text=LANGUAGES[current_language.get()]["previous"], command=previous_page)
prev_button.pack(side="left", padx=10)

page_label = Label(pagination_inner_frame, text=LANGUAGES[current_language.get()]['page'].format(page=current_page.get() + 1))
page_label.pack(side="left", padx=10)

next_button = Button(pagination_inner_frame, text=LANGUAGES[current_language.get()]["next"], command=next_page)
next_button.pack(side="left", padx=10)

status_bar = Label(root, textvariable=status_var, relief="sunken", anchor="w")
status_bar.pack(side="bottom", fill="x")

display_images(folder_path.get(), scrollable_frame, current_page, images_per_page, status_var, canvas.winfo_width())

root.mainloop()