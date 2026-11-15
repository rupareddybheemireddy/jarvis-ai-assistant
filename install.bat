
@echo off
setlocal

REM Always switch to the folder containing this installer
cd /d "%~dp0"

echo.
echo ==========================================
echo       JARVIS AI ASSISTANT SETUP
echo ==========================================
echo.

REM Check Python
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

REM Create virtual environment
echo.
echo Creating virtual environment...

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto error
) else (
    echo Virtual environment already exists.
)

REM Upgrade pip
echo.
echo Upgrading pip...

".venv\Scripts\python.exe" -m pip install --upgrade pip

if errorlevel 1 goto error

REM Install dependencies
echo.
echo Installing JARVIS dependencies...

".venv\Scripts\python.exe" -m pip install -r requirements.txt

if errorlevel 1 goto error

REM Verify dependencies
echo.
echo Checking installed packages...

".venv\Scripts\python.exe" -m pip check

if errorlevel 1 goto error

REM Create desktop shortcut
echo.
echo Creating JARVIS desktop shortcut...

set "JARVIS_DIR=%CD%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; try { $dir=$env:JARVIS_DIR; $shell=New-Object -ComObject WScript.Shell; $desktop=[Environment]::GetFolderPath('Desktop'); $shortcut=$shell.CreateShortcut((Join-Path $desktop 'JARVIS.lnk')); $shortcut.TargetPath=Join-Path $dir '.venv\Scripts\pythonw.exe'; $shortcut.Arguments=('"' + (Join-Path $dir 'jarvis_gui.py') + '"'); $shortcut.WorkingDirectory=$dir; $shortcut.Description='JARVIS AI Personal Assistant'; $shortcut.Save(); Write-Host 'Desktop shortcut created successfully.' } catch { Write-Host $_; exit 1 }"

if errorlevel 1 goto error

echo.
echo ==========================================
echo       INSTALLATION COMPLETED!
echo ==========================================
echo.
echo JARVIS has been installed successfully.
echo.
echo A JARVIS shortcut has been created on your desktop.
echo.
echo Double-click JARVIS to start the application.
echo.
pause
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
