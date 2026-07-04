# EasyPharma Wholesale - Desktop Application Build Guide

This guide explains how to convert your Django PWA app into a **Windows Desktop EXE** application using PyWebView and PyInstaller.

---

## Architecture

The desktop app works like this:

```
┌─────────────────────────────────────────────────┐
│           Desktop EXE (PyInstaller)             │
│                                                 │
│  ┌─────────────────┐   ┌─────────────────────┐  │
│  │  PyWebView Window │   │  Django Development  │  │
│  │  (Native GUI)     │◄──┤  Server (Background) │  │
│  │  localhost:8765   │   │  runs on localhost   │  │
│  └─────────────────┘   └─────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │  SQLite Database (db.sqlite3)             │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Windows 10/11** (or any OS that supports PyWebView)
- **Python 3.10+** installed and added to PATH
- Your project files (easy-pharma-wholesale folder)

---

## Step 1: Install Dependencies

Open a terminal/command prompt, navigate to your project folder, and run:

```bash
pip install pywebview pyinstaller django
```

---

## Step 2: Build the Desktop EXE

### Option A: Using the Batch File (Easiest)

Double-click `build_desktop.bat` or run it from command prompt:

```bash
build_desktop.bat
```

### Option B: Using Python Script

```bash
python build_desktop.py
```

### Option C: Manual PyInstaller Command

```bash
python -m PyInstaller --name EasyPharmaWholesale --onedir --clean --noconfirm --windowed --add-data "easyPharma_wholesale;easyPharma_wholesale" --add-data "wholesaleApp;wholesaleApp" --add-data "templates;templates" --add-data "static;static" --add-data "db.sqlite3;." --add-data "manage.py;." --hidden-import=django --hidden-import=django.core.management --hidden-import=django.core.management.commands --hidden-import=django.core.management.commands.runserver --hidden-import=django.contrib.admin --hidden-import=django.contrib.auth --hidden-import=django.contrib.contenttypes --hidden-import=django.contrib.sessions --hidden-import=django.contrib.messages --hidden-import=django.contrib.staticfiles --hidden-import=wholesaleApp --hidden-import=wholesaleApp.migrations --hidden-import=pywebview --hidden-import=webview --hidden-import=proxytools --hidden-import=sqlparse --exclude-module=tkinter --exclude-module=PIL --exclude-module=pillow gui.py
```

---

## Step 3: Find Your EXE

After a successful build, your desktop app will be in:

```
dist/EasyPharmaWholesale/EasyPharmaWholesale.exe
```

---

## How to Run

Simply double-click `EasyPharmaWholesale.exe`. A native desktop window will open displaying your EasyPharma Wholesale application.

---

## Development Mode (Without Building EXE)

For testing during development, you can run the desktop app directly:

```bash
python gui.py
```

This will start the Django server and open the PyWebView window without creating an EXE.

---

## Customization Options

### Change Window Title
Edit `gui.py` and modify the `title` parameter in `webview.create_window()`.

### Change Window Size
Edit `gui.py` and modify the `width` and `height` parameters.

### Change Port
Edit `gui.py` and modify the `PORT` variable (default: 8765).

### Add App Icon
1. Create a 256x256 .ico file
2. Set `APP_ICON` path in `build_desktop.py`
3. Rebuild the EXE

### Single File EXE
Edit `build_desktop.py` and change `--onedir` to `--onefile` in the build command.

---

## Important Notes

1. **Database**: The SQLite database (`db.sqlite3`) is included in the build. Data is preserved between runs.

2. **First Build**: The initial build may take a few minutes depending on your system.

3. **Antivirus**: Some antivirus software may flag the EXE as suspicious. Add it to exclusions or sign the executable.

4. **Distribution**: Distribute the entire `dist/EasyPharmaWholesale/` folder, not just the `.exe` file (if using `--onedir`).

5. **Data Backup**: The database file is included in the build. For persistent data, the app uses the database from its installation directory.

---

## Troubleshooting

### Build fails with "ModuleNotFoundError"
Run: `pip install --upgrade pyinstaller pyinstaller-hooks-contrib`

### EXE opens and closes immediately
Run the EXE from command prompt to see error messages:
```bash
dist/EasyPharmaWholesale/EasyPharmaWholesale.exe
```

### Port already in use
Change the `PORT` variable in `gui.py` to a different number.

### Blank window / white screen
Django server may not be starting. Check for errors in command prompt.

---

## Files Added for Desktop Build

| File | Purpose |
|------|---------|
| `gui.py` | Desktop launcher - starts Django server + opens PyWebView window |
| `build_desktop.py` | PyInstaller build configuration script |
| `build_desktop.bat` | Windows batch file for easy one-click building |

---

## Running the App After Distribution

Once you copy the `dist/EasyPharmaWholesale/` folder to another Windows machine, the user just needs to:

1. Copy the folder anywhere
2. Double-click `EasyPharmaWholesale.exe`
3. The app opens in a native desktop window

No Python, Django, or any other software needs to be installed on the user's machine!
