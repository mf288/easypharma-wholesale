@echo off
echo ============================================
echo Building EasyPharma Wholesale Desktop App
echo ============================================
echo.

echo [1/3] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
echo [2/3] Installing dependencies...
pip install pywebview pyinstaller django
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/3] Building desktop application...
python build_desktop.py

echo.
echo ============================================
echo Build Complete!
echo ============================================
echo.
echo Your desktop app is in the 'dist' folder:
echo   dist\EasyPharmaWholesale\EasyPharmaWholesale.exe
echo.
pause
