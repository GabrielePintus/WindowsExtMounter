# WSL Ext4 Mounter - PowerShell Launcher
# Automatically requests admin privileges if needed

param(
    [switch]$Force
)

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Requesting administrator privileges..." -ForegroundColor Yellow
    
    # Re-launch as administrator
    $scriptPath = $MyInvocation.MyCommand.Path
    Start-Process powershell.exe -ArgumentList "-ExecutionPolicy Bypass -File `"$scriptPath`" -Force" -Verb RunAs
    exit
}

Write-Host "WSL Ext4 Partition Mounter" -ForegroundColor Cyan
Write-Host "==========================`n" -ForegroundColor Cyan

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check PyQt6 installation
Write-Host "`nChecking dependencies..." -ForegroundColor Cyan
try {
    python -c "import PyQt6" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PyQt6 is installed" -ForegroundColor Green
    } else {
        throw "PyQt6 not found"
    }
} catch {
    Write-Host "PyQt6 is not installed. Installing now..." -ForegroundColor Yellow
    pip install PyQt6
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install PyQt6" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check WSL installation
Write-Host "`nChecking WSL installation..." -ForegroundColor Cyan
try {
    $wslVersion = wsl --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "WSL is installed" -ForegroundColor Green
    } else {
        Write-Host "WARNING: WSL may not be installed properly" -ForegroundColor Yellow
        Write-Host "Run 'wsl --install' to install WSL" -ForegroundColor Yellow
    }
} catch {
    Write-Host "WARNING: Could not verify WSL installation" -ForegroundColor Yellow
}

# Run the application
Write-Host "`nStarting WSL Ext4 Mounter...`n" -ForegroundColor Cyan
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "wsl_ext4_mounter.py"

if (-not (Test-Path $pythonScript)) {
    Write-Host "ERROR: wsl_ext4_mounter.py not found in script directory" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

try {
    python $pythonScript
} catch {
    Write-Host "`nERROR: Application crashed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

if (-not $Force) {
    Read-Host "`nPress Enter to exit"
}
