@echo off
setlocal

echo.
echo ==========================================
echo       JARVIS AI ASSISTANT SETUP
echo ==========================================
echo.

python --version
if errorlevel 1 (
    echo ERROR: Python is required.
    echo Install Python from https://www.python.org/downloads/
    echo Enable Add Python to PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 goto error
)

echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo.
echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error

echo.
echo ==========================================
echo       INSTALLATION COMPLETED
echo ==========================================
echo.
echo Start Jarvis using:
echo .venv\Scripts\python.exe jarvis_voice.py
echo.
echo Open the HUD:
echo jarvis_workplace.html
echo.
pause
exit /b 0

:error
echo.
echo INSTALLATION FAILED.
echo Check the error messages above.
pause
exit /b 1

