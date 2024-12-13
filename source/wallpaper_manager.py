### wallpaper_manager.py
import ctypes

class WallpaperManager:
    SPI_SETDESKWALLPAPER = 20

    @staticmethod
    def set_wallpaper(image_path):
        try:
            ctypes.windll.user32.SystemParametersInfoW(WallpaperManager.SPI_SETDESKWALLPAPER, 0, image_path, 3)
            return True, ""
        except Exception as e:
            return False, str(e)