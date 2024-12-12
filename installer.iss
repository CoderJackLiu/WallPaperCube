[Setup]
AppName=WallpaperCube
AppVersion=1.0
DefaultDirName={pf}\\WallpaperCube
DefaultGroupName=WallpaperCube
OutputBaseFilename=WallpaperCubeInstaller
Compression=lzma2
SolidCompression=yes
SetupIconFile=E:\Projects\WallPaperCube\icon.ico

[Files]
Source: "E:\Projects\WallPaperCube\dist\WallPaperCube.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\Projects\WallPaperCube\dist\config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "E:\Projects\WallPaperCube\icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\WallpaperCube"; Filename: "{app}\WallPaperCube.exe"
Name: "{userdesktop}\WallpaperCube"; Filename: "{app}\WallPaperCube.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop icon"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Run]
Filename: "{app}\WallPaperCube.exe"; Description: "Launch WallpaperCube"; Flags: nowait postinstall skipifsilent
