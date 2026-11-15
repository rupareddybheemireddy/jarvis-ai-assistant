
@echo off
setlocal

cd /d "%~dp0"

echo.
echo ==========================================
echo       JARVIS AI ASSISTANT SETUP
echo ==========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 goto error

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
