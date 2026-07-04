#!/usr/bin/env python
"""
EasyPharma Wholesale - Desktop Application Launcher
This script starts the Django development server in the background
and opens the app in a native desktop window using pywebview.
"""

import os
import sys
import time
import threading
import webview


# ─── Determine paths (works for both dev and PyInstaller-frozen builds) ───
if getattr(sys, 'frozen', False):
    # Running from PyInstaller bundle
    BASE_DIR = sys._MEIPASS  # noqa: F821
    MANAGE_DIR = os.path.dirname(sys.executable)
else:
    # Running from source
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    MANAGE_DIR = BASE_DIR

DJANGO_SETTINGS_MODULE = 'easyPharma_wholesale.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS_MODULE)

PORT = 8765  # Use a non-standard port to avoid conflicts


# ─── Start Django Development Server ───
def start_django_server():
    """Start the Django runserver in a background thread."""
    # Add project directory to sys.path so Django can find settings
    if MANAGE_DIR not in sys.path:
        sys.path.insert(0, MANAGE_DIR)

    from django.core.management import call_command
    print(f"Starting Django server on 127.0.0.1:{PORT}...")
    try:
        call_command('runserver', f'127.0.0.1:{PORT}', use_reloader=False)
    except SystemExit:
        pass


# ─── Start PyWebView Desktop Window ───
def start_webview():
    """Wait for Django server then open the webview window."""
    # Wait for server to be ready (max 10 seconds)
    url = f'http://127.0.0.1:{PORT}/'
    max_wait = 10
    waited = 0
    import urllib.request

    while waited < max_wait:
        try:
            urllib.request.urlopen(url, timeout=1)
            break
        except Exception:
            time.sleep(0.5)
            waited += 0.5

    if waited >= max_wait:
        print("Warning: Django server may not have started. Trying anyway...")

    print(f"Opening EasyPharma Wholesale in desktop window...")
    window = webview.create_window(
        'EasyPharma Wholesale',
        url,
        width=1200,
        height=800,
        min_size=(900, 600),
        confirm_close=True,
    )
    webview.start()
    # When window closes, exit the process
    os._exit(0)


# ─── Main Entry Point ───
if __name__ == '__main__':
    # Launch Django server in a daemon thread
    server_thread = threading.Thread(target=start_django_server, daemon=True)
    server_thread.start()

    # Give server a moment to start before launching webview
    time.sleep(1)

    # Start the desktop webview window (blocks until closed)
    start_webview()
