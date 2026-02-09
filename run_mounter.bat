@echo off
:: WSL Ext4 Mounter - Run as Administrator
:: This script automatically requests admin privileges and runs the application

echo WSL Ext4 Partition Mounter
echo ===========================
echo.

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
    echo.
    goto :run
) else (
    echo Requesting administrator privileges...
    echo.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:run
:: Check if Python is installed
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    pause
    exit /b 1
)

:: Check if PyQt6 is installed
python -c "import PyQt6" >nul 2>&1
if %errorLevel% neq 0 (
    echo PyQt6 is not installed. Installing now...
    echo.
    pip install PyQt6
    if %errorLevel% neq 0 (
        echo ERROR: Failed to install PyQt6
        pause
        exit /b 1
    )
)

:: Run the application
echo Starting WSL Ext4 Mounter...
echo.
python "%~dp0wsl_ext4_mounter.py"

if %errorLevel% neq 0 (
    echo.
    echo ERROR: Application exited with error code %errorLevel%
    pause
)
