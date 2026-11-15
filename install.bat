
@echo off
setlocal

REM Always switch to the folder containing this installer
cd /d "%~dp0"

echo.
echo ==========================================
echo       JARVIS AI ASSISTANT SETUP
echo ==========================================
echo.

echo Checking Python installation...
python --version

if errorlevel 1 (
    echo.
    echo ERROR: Python is required.
    echo Install Python 3.11 from:
    echo https://www.python.org/downloads/
    echo Remember to enable Add Python to PATH.
    goto error
)

echo.
echo Creating virtual environment...

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto error
) else (
    echo Virtual environment already exists.
)

echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

if errorlevel 1 goto error

echo.
echo Installing JARVIS dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 goto error

echo.
echo Checking installed packages...
".venv\Scripts\python.exe" -m pip check

if errorlevel 1 goto error

echo.
echo ==========================================
echo       INSTALLATION COMPLETED!
echo ==========================================
echo.
echo JARVIS has been installed successfully.
echo.
echo To start JARVIS, run:
echo .venv\Scripts\python.exe jarvis_gui.py
echo.
echo Press any key to close this installer.
pause >nul
exit /b 0

:error
echo.
echo ==========================================
echo       INSTALLATION FAILED!
echo ==========================================
echo Please check the error messages above.
echo.
pause
exit /b 1
