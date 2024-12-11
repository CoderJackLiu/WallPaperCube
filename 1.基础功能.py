import os
import ctypes
from tkinter import Tk, filedialog, Label, Button, Frame, StringVar, Canvas, Scrollbar, messagebox
from PIL import Image, ImageTk
from pathlib import Path
import tkinter as tk

# Function to set wallpaper on Windows
def set_wallpaper(image_path):
    SPI_SETDESKWALLPAPER = 20
    try:
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, image_path, 3)
        print(f"Wallpaper set to: {image_path}")
    except Exception as e:
        print(f"Failed to set wallpaper: {e}")

# Function to list all images in a folder
def get_images_in_folder(folder_path):
    try:
        return [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    except Exception as e:
        print(f"Error: {e}")
        return []

# Function to display image thumbnails
def display_images(folder, canvas, scrollable_frame):
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    images = get_images_in_folder(folder)

    for index, image_path in enumerate(images):
        try:
            with Image.open(image_path) as img:
                img.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img)
            img_label = Label(scrollable_frame, image=photo, text=Path(image_path).name, compound="top")
            img_label.photo = photo  # Keep reference to prevent garbage collection
            img_label.grid(row=index // 5, column=index % 5, padx=5, pady=5)

            def set_wallpaper_for_image(path=image_path):
                set_wallpaper(path)
                messagebox.showinfo("Success", f"Wallpaper set to: {os.path.basename(path)}")

            img_label.bind("<Button-1>", lambda event, p=image_path: set_wallpaper_for_image(p))

        except Exception as e:
            print(f"Failed to load image {image_path}: {e}")

# GUI Application
def start_application():
    def select_folder():
        folder = filedialog.askdirectory(title="Select Wallpaper Folder")
        if folder:
            folder_path.set(folder)
            display_images(folder, canvas, scrollable_frame)

    root = Tk()
    root.title("Wallpaper Changer")
    root.geometry("800x600")

    folder_path = StringVar()

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

    root.mainloop()

if __name__ == "__main__":
    start_application()
