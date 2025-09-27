#!/usr/bin/env python3
"""
Build script for creating Windows executable of PwnSafe.
This script creates a standalone .exe file that can run on Windows without Python installed.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_windows_executable():
    """Build Windows executable using PyInstaller."""
    print("🔧 Building PwnSafe for Windows...")
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # PyInstaller command for Windows
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--windowed",                   # Hide console window (GUI app)
        "--name=PwnSafe",               # Name of the executable
        "--icon=icon.ico",              # Icon file (if exists)
        "--add-data=README.md;.",       # Include README
        "--hidden-import=customtkinter",
        "--hidden-import=paramiko",
        "--hidden-import=cryptography",
        "--hidden-import=bcrypt",
        "--hidden-import=PyNaCl",
        "--hidden-import=cffi",
        "--hidden-import=pycparser",
        "--hidden-import=packaging",
        "--hidden-import=darkdetect",
        "--clean",                      # Clean cache
        "pwnsafe.py"
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Windows executable built successfully!")
        print(f"📁 Executable location: {script_dir / 'dist' / 'PwnSafe.exe'}")
        
        # Create a simple batch file to run the executable
        batch_content = """@echo off
echo Starting PwnSafe...
PwnSafe.exe
pause
"""
        with open(script_dir / "dist" / "run_pwnsafe.bat", "w") as f:
            f.write(batch_content)
        
        print("📄 Created run_pwnsafe.bat for easy execution")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def create_installer_script():
    """Create a simple installer script."""
    installer_content = """@echo off
echo ========================================
echo    PwnSafe v1.0.0 - Professional Edition
echo ========================================
echo.
echo Installing PwnSafe...
echo.

REM Create installation directory
if not exist "%USERPROFILE%\\PwnSafe" mkdir "%USERPROFILE%\\PwnSafe"

REM Copy executable
copy "PwnSafe.exe" "%USERPROFILE%\\PwnSafe\\"

REM Create desktop shortcut (requires admin rights)
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\PwnSafe.lnk'); $Shortcut.TargetPath = '%USERPROFILE%\\PwnSafe\\PwnSafe.exe'; $Shortcut.Save()"

echo.
echo ========================================
echo    Installation Complete!
echo ========================================
echo.
echo PwnSafe has been installed to:
echo %USERPROFILE%\\PwnSafe\\
echo.
echo A desktop shortcut has been created.
echo.
echo Double-click PwnSafe.exe to run the application.
echo.
pause
"""
    
    with open("install_pwnsafe.bat", "w") as f:
        f.write(installer_content)
    
    print("📄 Created install_pwnsafe.bat installer script")

if __name__ == "__main__":
    print("🚀 PwnSafe Windows Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✅ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build the executable
    if build_windows_executable():
        create_installer_script()
        print("\n🎉 Build process completed successfully!")
        print("\nFiles created:")
        print("  📁 dist/PwnSafe.exe - Main executable")
        print("  📄 dist/run_pwnsafe.bat - Easy run script")
        print("  📄 install_pwnsafe.bat - Installer script")
        print("\nTo distribute:")
        print("  1. Copy the entire 'dist' folder")
        print("  2. Or use the installer script")
    else:
        print("\n❌ Build process failed!")
        sys.exit(1)
