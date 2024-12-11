import os
import ctypes
import json
import threading
from tkinter import Tk, filedialog, Label, Button, Frame, StringVar, Canvas, Scrollbar, Toplevel, Radiobutton
from PIL import Image, ImageTk
from pathlib import Path
import hashlib
import tkinter as tk
import math

# Config file for storing folder path
CONFIG_FILE = "config.json"
THUMBNAIL_DIR = "thumbnails"
DEFAULT_FOLDER = os.path.expanduser("~/Pictures")

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
    return {"last_folder": DEFAULT_FOLDER, "theme": "day"}

# Function to set wallpaper on Windows
def set_wallpaper(image_path, status_var):
    SPI_SETDESKWALLPAPER = 20
    try:
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
        status_var.set(f"Wallpaper set to: {os.path.basename(image_path)}")
    except Exception as e:
        status_var.set(f"Failed to set wallpaper: {e}")

# Function to list all images in a folder
def get_images_in_folder(folder_path):
    try:
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    except Exception as e:
        print(f"Error: {e}")
        return []

# Function to generate or fetch cached thumbnail
def generate_thumbnail(image_path):
    if not os.path.exists(THUMBNAIL_DIR):
        os.makedirs(THUMBNAIL_DIR)

    # Create a unique identifier using file path and modification time
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

# Function to dynamically adjust layout based on window size
def update_wrapbox(scrollable_frame, images, canvas_width, status_var):
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    columns = max(canvas_width // 120, 1)  # Calculate number of columns based on available width

    def on_hover(event):
        event.widget.config(bg="#d3d3d3")

    def on_leave(event):
        event.widget.config(bg="white")

    def on_click(event, path):
        event.widget.config(bg="#a9a9a9")
        set_wallpaper(path, status_var)

    for index, (image_path, thumbnail) in enumerate(images):
        img_label = Label(scrollable_frame, image=thumbnail, text=Path(image_path).name, compound="top", bg="white")
        img_label.photo = thumbnail  # Keep reference to prevent garbage collection
        img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)

        # Add hover and click events
        img_label.bind("<Enter>", on_hover)
        img_label.bind("<Leave>", on_leave)
        img_label.bind("<Button-1>", lambda event, path=image_path: on_click(event, path))

# Function to display paginated image thumbnails
def display_images(folder, scrollable_frame, page, images_per_page, status_var, canvas_width):
    images = get_images_in_folder(folder)
    total_images = len(images)
    max_page = math.ceil(total_images / images_per_page) - 1

    if page > max_page:
        page = max_page
        current_page.set(page)

    start_index = page * images_per_page
    end_index = min(start_index + images_per_page, total_images)
    loaded_images = [(image_path, generate_thumbnail(image_path)) for image_path in images[start_index:end_index]]
    update_wrapbox(scrollable_frame, loaded_images, canvas_width, status_var)

# Asynchronous thumbnail generation
def preload_thumbnails(folder):
    images = get_images_in_folder(folder)
    for image_path in images:
        generate_thumbnail(image_path)

# Function to apply the theme
def apply_theme(theme):
    if theme == "day":
        root.configure(bg="white")
    elif theme == "night":
        root.configure(bg="#2c2c2c")

# Function to open theme settings panel
def open_theme_settings():
    def save_and_apply_theme():
        selected_theme = theme_var.get()
        config["theme"] = selected_theme
        save_config(config)
        apply_theme(selected_theme)
        settings_window.destroy()

    settings_window = Toplevel(root)
    settings_window.title("Theme Settings")
    settings_window.geometry("300x150")

    theme_var = StringVar(value=config.get("theme", "day"))

    Radiobutton(settings_window, text="Day", variable=theme_var, value="day").pack(anchor="w", pady=5)
    Radiobutton(settings_window, text="Night", variable=theme_var, value="night").pack(anchor="w", pady=5)

    Button(settings_window, text="Apply", command=save_and_apply_theme).pack(pady=10)

# GUI Application
def start_application():
    def select_folder():
        folder = filedialog.askdirectory(title="Select Wallpaper Folder")
        if folder:
            folder_path.set(folder)
            config["last_folder"] = folder
            save_config(config)
            threading.Thread(target=preload_thumbnails, args=(folder,), daemon=True).start()
            display_images(folder, scrollable_frame, current_page.get(), images_per_page, status_var, canvas.winfo_width())

    def next_page():
        if folder_path.get():
            images = get_images_in_folder(folder_path.get())
            max_page = math.ceil(len(images) / images_per_page) - 1
            if current_page.get() < max_page:
                current_page.set(current_page.get() + 1)
                display_images(folder_path.get(), scrollable_frame, current_page.get(), images_per_page, status_var, canvas.winfo_width())
                page_label.config(text=f"Page {current_page.get() + 1}")

    def previous_page():
        if folder_path.get() and current_page.get() > 0:
            current_page.set(current_page.get() - 1)
            display_images(folder_path.get(), scrollable_frame, current_page.get(), images_per_page, status_var, canvas.winfo_width())
            page_label.config(text=f"Page {current_page.get() + 1}")

    def on_resize(event):
        if folder_path.get():
            display_images(folder_path.get(), scrollable_frame, current_page.get(), images_per_page, status_var, event.width)

    global root, config
    root = Tk()
    root.title("Wallpaper Changer")

    # Center window on screen
    window_width, window_height = 800, 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = (screen_height // 2) - (window_height // 2)
    position_right = (screen_width // 2) - (window_width // 2)
    root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

    config = load_config()
    apply_theme(config.get("theme", "day"))

    folder_path = StringVar(value=config.get("last_folder", DEFAULT_FOLDER))
    if not os.path.exists(folder_path.get()):
        folder_path.set(DEFAULT_FOLDER)
        status_var = StringVar(value=f"Default path set to {DEFAULT_FOLDER}. Please select a folder.")
    else:
        status_var = StringVar(value="Ready")

    current_page = tk.IntVar(value=0)
    images_per_page = 24

    # Top frame for folder selection
    top_frame = Frame(root)
    top_frame.pack(fill="x", padx=10, pady=5)

    Label(top_frame, text="Wallpaper Folder:").pack(side="left")
    Button(top_frame, text="Select Folder", command=select_folder).pack(side="left", padx=5)
    Button(top_frame, text="Theme Settings", command=open_theme_settings).pack(side="right")

    # Scrollable canvas for displaying images
    canvas_frame = Frame(root)
    canvas_frame.pack(fill="both", expand=True, padx=10, pady=5)

    canvas = Canvas(canvas_frame)
    scrollbar = Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = Frame(canvas)

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Bind resize event
    canvas.bind("<Configure>", on_resize)

    # Pagination controls
    pagination_frame = Frame(root)
    pagination_frame.pack(fill="x", padx=10, pady=5)

    pagination_inner_frame = Frame(pagination_frame)
    pagination_inner_frame.pack(anchor="center")

    prev_button = Button(pagination_inner_frame, text="Previous", command=previous_page)
    prev_button.pack(side="left", padx=10)

    page_label = Label(pagination_inner_frame, text=f"Page {current_page.get() + 1}")
    page_label.pack(side="left", padx=10)

    next_button = Button(pagination_inner_frame, text="Next", command=next_page)
    next_button.pack(side="left", padx=10)

    # Status bar
    status_bar = Label(root, textvariable=status_var, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")

    # Preload thumbnails if a folder was persisted
    if folder_path.get():
        threading.Thread(target=preload_thumbnails, args=(folder_path.get(),), daemon=True).start()
        display_images(folder_path.get(), scrollable_frame, current_page.get(), images_per_page, status_var, canvas.winfo_width())

    root.mainloop()

if __name__ == "__main__":
    start_application()