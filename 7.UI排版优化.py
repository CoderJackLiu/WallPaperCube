import os
import ctypes
import json
import threading
from tkinter import Tk, filedialog, Label, Button, Frame, StringVar, Canvas, Scrollbar
from PIL import Image, ImageTk
from pathlib import Path
import tkinter as tk

# Config file for storing folder path
CONFIG_FILE = "config.json"
THUMBNAIL_DIR = "thumbnails"

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

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

    thumbnail_path = os.path.join(THUMBNAIL_DIR, f"{Path(image_path).stem}_thumbnail.png")
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
def update_wrapbox(scrollable_frame, images, canvas_width):
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    columns = max(canvas_width // 120, 1)  # Calculate number of columns based on available width

    for index, (image_path, thumbnail) in enumerate(images):
        img_label = Label(scrollable_frame, image=thumbnail, text=Path(image_path).name, compound="top")
        img_label.photo = thumbnail  # Keep reference to prevent garbage collection
        img_label.grid(row=index // columns, column=index % columns, padx=10, pady=10)

# Function to display paginated image thumbnails
def display_images(folder, scrollable_frame, page, images_per_page, status_var, canvas_width):
    images = get_images_in_folder(folder)
    start_index = page * images_per_page
    end_index = start_index + images_per_page
    loaded_images = [(image_path, generate_thumbnail(image_path)) for image_path in images[start_index:end_index]]
    update_wrapbox(scrollable_frame, loaded_images, canvas_width)

# Asynchronous thumbnail generation
def preload_thumbnails(folder):
    images = get_images_in_folder(folder)
    for image_path in images:
        generate_thumbnail(image_path)

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
            max_page = len(images) // images_per_page
            if current_page.get() < max_page:
                current_page.set(current_page.get() + 1)
                display_images(folder_path.get(), scrollable_frame, current_page.get(), images_per_page, status_var, canvas.winfo_width())

    def previous_page():
        if folder_path.get() and current_page.get() > 0:
            current_page.set(current_page.get() - 1)
            display_images(folder_path.get(), scrollable_frame, current_page.get(), images_per_page, status_var, canvas.winfo_width())

    def on_resize(event):
        if folder_path.get():
            display_images(folder_path.get(), scrollable_frame, current_page.get(), images_per_page, status_var, event.width)

    root = Tk()
    root.title("Wallpaper Changer")
    root.geometry("800x600")

    config = load_config()
    folder_path = StringVar(value=config.get("last_folder", ""))
    current_page = tk.IntVar(value=0)
    images_per_page = 20
    status_var = StringVar(value="Ready")

    # Top frame for folder selection
    top_frame = Frame(root)
    top_frame.pack(fill="x", padx=10, pady=5)

    Label(top_frame, text="Wallpaper Folder:").pack(side="left")
    Button(top_frame, text="Select Folder", command=select_folder).pack(side="right")

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

    Button(pagination_frame, text="Previous", command=previous_page).pack(side="left")
    Button(pagination_frame, text="Next", command=next_page).pack(side="right")

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