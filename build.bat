@echo off
chcp 65001 >nul
echo Building ModeCalc.exe ...
python -m PyInstaller --name "ModeCalc" --icon static/icon.ico --noconsole --onefile --version-file version_info.txt --add-data "static;static" --hidden-import webview.platforms.edgechromium --hidden-import mido --hidden-import mido.backends.rtmidi --hidden-import rtmidi app.py
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Make sure dependencies are installed:
    echo         pip install -r requirements.txt
    pause
    exit /b 1
)
echo.
echo Done. Output: dist\ModeCalc.exe
pause
