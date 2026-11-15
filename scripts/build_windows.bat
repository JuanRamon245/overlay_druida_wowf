@echo off
rem Construye dist\FeralCompanion.exe (portable, un solo archivo).
rem Uso: doble clic o "scripts\build_windows.bat" desde la carpeta del proyecto.
setlocal
cd /d "%~dp0.."

if not exist .venv\Scripts\python.exe (
    echo Creando entorno virtual...
    python -m venv .venv || goto :error
)
.venv\Scripts\python -m pip install --quiet --upgrade pip
.venv\Scripts\python -m pip install --quiet -r requirements.txt pyinstaller pytest || goto :error

echo Ejecutando tests...
.venv\Scripts\python -m pytest -q || goto :error

.venv\Scripts\python scripts\make_icon.py || goto :error

.venv\Scripts\pyinstaller --noconfirm --clean --onefile --windowed ^
    --name FeralCompanion ^
    --icon assets\icon.ico ^
    --paths src ^
    --add-data "content;content" ^
    --add-data "assets;assets" ^
    --exclude-module PySide6.QtNetwork ^
    --exclude-module PySide6.QtQml ^
    --exclude-module PySide6.QtQuick ^
    --exclude-module PySide6.QtOpenGL ^
    --exclude-module PySide6.QtPdf ^
    --exclude-module tkinter ^
    src\main.py || goto :error

echo.
echo Listo: dist\FeralCompanion.exe
exit /b 0

:error
echo.
echo ERROR durante la construccion.
exit /b 1
