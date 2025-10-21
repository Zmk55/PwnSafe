# PwnSafe Compact UI Launcher
# PowerShell script to easily run PwnSafe with the new compact UI

Write-Host "🚀 Starting PwnSafe with Compact UI..." -ForegroundColor Green

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run the application
python pwnsafe.py

Write-Host "PwnSafe has closed." -ForegroundColor Yellow
