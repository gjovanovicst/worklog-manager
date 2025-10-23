@echo off
REM Worklog Manager - Development Mode Launcher (Windows)
REM This script starts the application with auto-reload on file changes

echo Starting Worklog Manager in Development Mode...
echo ==============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Check if watchdog is installed
python -c "import watchdog" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: watchdog package not installed
    echo    Auto-reload will not work without it
    echo.
    echo Install it with:
    echo    pip install watchdog
    echo    or
    echo    pip install -r requirements.txt
    echo.
    set /p CONTINUE="Continue anyway? (y/N) "
    if /i not "%CONTINUE%"=="y" (
        exit /b 1
    )
)

REM Run the development script
cd /d "%SCRIPT_DIR%"
python dev_start.py %*

if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error.
    pause
)
