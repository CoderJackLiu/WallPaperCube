<!-- Tab Navigation -->
<div id="tab-container" style="display: flex; justify-content: flex-start; border-bottom: 1px solid #ddd;">
  <button onclick="showTab('english')" style="margin-right: 10px; cursor: pointer;">English</button>
  <button onclick="showTab('chinese')" style="cursor: pointer;">中文</button>
</div>

<div id="english" style="display: block; padding: 10px;">
  
# WallpaperCube (English Version)

WallpaperCube is a desktop wallpaper management application designed to enhance your experience with wallpapers. With an intuitive interface and powerful features, WallpaperCube makes it easy to organize, select, and customize your wallpapers to suit your preferences.

## Current Features

- **Folder Selection:** Choose a folder containing your wallpapers and manage them within the app.
- **Thumbnail Previews:** Quickly view thumbnails of all wallpapers in the selected folder.
- **Wallpaper Application:** Apply a selected wallpaper to your desktop with a single click.
- **Language Support:** Switch between multiple languages for the user interface (currently supports English and Chinese).
- **Customizable UI:** Easy-to-use settings to adjust app behavior and appearance.

### English Interface
![English Interface](assets/WallPaper-en.jpg)

</div>

<div id="chinese" style="display: none; padding: 10px;">

# WallpaperCube (中文版)

WallpaperCube 是一个桌面壁纸管理应用程序，旨在提升您使用壁纸的体验。通过直观的界面和强大的功能，WallpaperCube 让您轻松地组织、选择和定制壁纸，以满足您的偏好。

## 当前功能

- **文件夹选择：** 选择包含壁纸的文件夹，并在应用中进行管理。
- **缩略图预览：** 快速查看所选文件夹中所有壁纸的缩略图。
- **壁纸应用：** 一键将选定的壁纸设置为桌面背景。
- **多语言支持：** 支持多语言界面切换（目前支持英文和中文）。
- **自定义界面：** 简单易用的设置界面，用于调整应用的行为和外观。

### 中文界面
![中文界面](assets/WallPaper-zh.jpg)

</div>

<script>
function showTab(tabId) {
  document.getElementById('english').style.display = tabId === 'english' ? 'block' : 'none';
  document.getElementById('chinese').style.display = tabId === 'chinese' ? 'block' : 'none';
}
</script>
