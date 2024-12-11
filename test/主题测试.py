import os
import json
from tkinter import Tk, Toplevel, Radiobutton, StringVar, Button, Frame, Label

CONFIG_FILE = "../config.json"

# Function to save configuration
def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

# Function to load configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            try:
                return json.load(file)
            except Exception as e:
                print(f"Error loading config: {e}")
    return {"theme": "day"}

# Function to apply the theme
def apply_theme(theme, root):
    if theme == "day":
        root.configure(bg="white")
    elif theme == "night":
        root.configure(bg="black")

# Function to open theme settings panel
def open_theme_settings(root, config):
    def save_and_apply_theme():
        selected_theme = theme_var.get()
        config["theme"] = selected_theme
        save_config(config)
        apply_theme(selected_theme, root)
        settings_window.destroy()

    settings_window = Toplevel(root)
    settings_window.title("Theme Settings")
    settings_window.geometry("300x150")

    theme_var = StringVar(value=config.get("theme", "day"))

    Radiobutton(settings_window, text="Day", variable=theme_var, value="day").pack(anchor="w", pady=5)
    Radiobutton(settings_window, text="Night", variable=theme_var, value="night").pack(anchor="w", pady=5)

    Button(settings_window, text="Apply", command=save_and_apply_theme).pack(pady=10)

# Main application function
def start_application():
    root = Tk()
    root.title("Theme Settings Example")
    root.geometry("400x300")

    config = load_config()
    apply_theme(config.get("theme", "day"), root)

    frame = Frame(root)
    frame.pack(pady=50)

    Label(frame, text="Theme Settings Example", font=("Arial", 16)).pack()
    Button(frame, text="Open Theme Settings", command=lambda: open_theme_settings(root, config)).pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    start_application()