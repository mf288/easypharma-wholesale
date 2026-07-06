#!/usr/bin/env python
"""
Build script for EasyPharma Wholesale Desktop EXE.
Uses PyInstaller to package the Django app + PyWebView into a single Windows executable.

Usage:
    python build_desktop.py

Requirements:
    - Must be run on Windows (or cross-compile environment)
    - pip install pyinstaller pywebview django
"""

import os
import sys
import subprocess

# ─── Configuration ───
APP_NAME = "EasyPharmaWholesale"
GUI_SCRIPT = "gui.py"
APP_ICON = None  # Set path to .ico file if you have one
Django_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Files and directories to include ───
DATA_FILES = [
    # Django project directories
    ('easyPharma_wholesale', 'easyPharma_wholesale'),
    ('wholesaleApp', 'wholesaleApp'),
    ('templates', 'templates'),
    ('static', 'static'),
    # SQLite database (will be copied at runtime if needed)
    ('db.sqlite3', 'db.sqlite3'),
    # Django management script
    ('manage.py', 'manage.py'),
]

# ─── Build command ───
cmd = [
    sys.executable, '-m', 'PyInstaller',
    # Output options
    '--name', APP_NAME,
    '--onedir',  # one directory (more reliable for Django)
    # '--onefile',  # Uncomment for single-file EXE (slower startup)
    '--clean',
    '--noconfirm',
    # Window options
    '--windowed',  # No console window
    '--icon', APP_ICON if APP_ICON else 'NONE',
    # Data files to bundle
    *(f'--add-data={src}{os.pathsep}{dest}' for src, dest in DATA_FILES),
    # Hidden imports that PyInstaller might miss
    '--hidden-import=django',
    '--hidden-import=django.core.management',
    '--hidden-import=django.core.management.commands',
    '--hidden-import=django.core.management.commands.runserver',
    '--hidden-import=django.contrib.admin',
    '--hidden-import=django.contrib.auth',
    '--hidden-import=django.contrib.contenttypes',
    '--hidden-import=django.contrib.sessions',
    '--hidden-import=django.contrib.messages',
    '--hidden-import=django.contrib.staticfiles',
    '--hidden-import=wholesaleApp',
    '--hidden-import=wholesaleApp.migrations',
    '--hidden-import=pywebview',
    '--hidden-import=webview',
    '--hidden-import=proxytools',
    '--hidden-import=sqlparse',
    # Exclude unnecessary modules to reduce size
    '--exclude-module=tkinter',
    '--exclude-module=PIL',
    '--exclude-module=pillow',
    # The main script
    GUI_SCRIPT,
]

# Remove icon flag if no icon
if not APP_ICON:
    cmd.remove('--icon')
    cmd.remove('NONE')

print("=" * 60)
print("Building EasyPharma Wholesale Desktop App")
print("=" * 60)
print(f"Command: {' '.join(cmd)}")
print()

# ─── Run PyInstaller ───
result = subprocess.run(cmd, cwd=Django_PROJECT_DIR)

if result.returncode == 0:
    print("\n" + "=" * 60)
    print("Build successful!")
    print(f"Executable location: {os.path.join(Django_PROJECT_DIR, 'dist', APP_NAME)}")
    print("=" * 60)
else:
    print("\n" + "=" * 60)
    print("Build failed! Check the output above for errors.")
    print("=" * 60)

sys.exit(result.returncode)
