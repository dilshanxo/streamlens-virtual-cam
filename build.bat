@echo off
setlocal

echo =========================================
echo StreamLens Build Automation Script
echo =========================================
echo.

if not exist venv (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
) else (
    echo [INFO] Virtual environment 'venv' already exists.
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing requirements...
pip install -r requirements.txt

echo [INFO] Installing PyInstaller...
pip install pyinstaller

echo [INFO] Setting PYTHONPATH...
set PYTHONPATH=%cd%\src

echo [INFO] Compiling StreamLens...
pyinstaller --noconsole --onefile --name="stream_lens_v1.0.4" --icon="assets/icon.ico" --add-data "assets;assets" src/ui_main.py

if %ERRORLEVEL% equ 0 (
    echo.
    echo =========================================
    echo Build Successful! Check the dist/ folder.
    echo =========================================
) else (
    echo.
    echo =========================================
    echo Build Failed! Check the logs above.
    echo =========================================
)

pause
