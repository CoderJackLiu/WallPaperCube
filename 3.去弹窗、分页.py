import os
import ctypes
from tkinter import Tk, filedialog, Label, Button, Frame, StringVar, Canvas, Scrollbar
from PIL import Image, ImageTk
from pathlib import Path
import tkinter as tk

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

# Function to display paginated image thumbnails
def display_images(folder, canvas, scrollable_frame, page, images_per_page, status_var, root):
    for widget in scrollable_frame.winfo_children():
        widget.destroy()

    images = get_images_in_folder(folder)
    start_index = page * images_per_page
    end_index = start_index + images_per_page

    for index, image_path in enumerate(images[start_index:end_index]):
        try:
            with Image.open(image_path) as img:
                img.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(img)
            img_label = Label(scrollable_frame, image=photo, text=Path(image_path).name, compound="top")
            img_label.photo = photo  # Keep reference to prevent garbage collection
            img_label.grid(row=index // 5, column=index % 5, padx=5, pady=5)

            def set_wallpaper_for_image(path=image_path):
                # Disable UI interactions
                root.config(cursor="wait")
                set_wallpaper(path, status_var)
                root.config(cursor="")  # Re-enable UI interactions

            img_label.bind("<Button-1>", lambda event, p=image_path: set_wallpaper_for_image(p))

        except Exception as e:
            print(f"Failed to load image {image_path}: {e}")

# GUI Application
def start_application():
    def select_folder():
        folder = filedialog.askdirectory(title="Select Wallpaper Folder")
        if folder:
            folder_path.set(folder)
            display_images(folder, canvas, scrollable_frame, current_page.get(), images_per_page, status_var, root)

    def next_page():
        if folder_path.get():
            images = get_images_in_folder(folder_path.get())
            max_page = len(images) // images_per_page
            if current_page.get() < max_page:
                current_page.set(current_page.get() + 1)
                display_images(folder_path.get(), canvas, scrollable_frame, current_page.get(), images_per_page, status_var, root)

    def previous_page():
        if folder_path.get() and current_page.get() > 0:
            current_page.set(current_page.get() - 1)
            display_images(folder_path.get(), canvas, scrollable_frame, current_page.get(), images_per_page, status_var, root)

    root = Tk()
    root.title("Wallpaper Changer")
    root.geometry("800x600")

    folder_path = StringVar()
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

    # Pagination controls
    pagination_frame = Frame(root)
    pagination_frame.pack(fill="x", padx=10, pady=5)

    Button(pagination_frame, text="Previous", command=previous_page).pack(side="left")
    Button(pagination_frame, text="Next", command=next_page).pack(side="right")

    # Status bar
    status_bar = Label(root, textvariable=status_var, relief="sunken", anchor="w")
    status_bar.pack(side="bottom", fill="x")

    root.mainloop()

if __name__ == "__main__":
    start_application()
