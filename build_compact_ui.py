#!/usr/bin/env python3
"""
Build script for creating Windows executable with the new compact UI.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(errors="replace")

def build_compact_ui_executable():
    """Build Windows executable with the new compact UI."""
    print("Building PwnSafe with Compact UI for Windows...")
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # PyInstaller command for Windows with new UI
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--windowed",                   # Hide console window (GUI app)
        "--name=PwnSafe-Compact",       # Name of the executable
        "--icon=icon.ico",              # Icon file (if exists)
        "--add-data=README.md;.",       # Include README
        "--add-data=drivers;drivers",   # Include RNDIS driver package
        "--add-data=scripts/win_connection_share.ps1;scripts",  # Include Windows ICS setup script
        "--hidden-import=customtkinter",
        "--hidden-import=paramiko",
        "--hidden-import=cryptography",
        "--hidden-import=bcrypt",
        "--hidden-import=nacl",
        "--hidden-import=cffi",
        "--hidden-import=pycparser",
        "--hidden-import=packaging",
        "--hidden-import=darkdetect",
        "--hidden-import=wmi",
        "--hidden-import=pythoncom",
        "--hidden-import=ui_components",
        "--hidden-import=profile_manager",
        "--hidden-import=ssh_auth_enhanced",
        "--clean",                      # Clean cache
        "pwnsafe.py"
    ]
    
    # Remove icon parameter if icon file doesn't exist
    if not os.path.exists("icon.ico"):
        cmd = [arg for arg in cmd if not arg.startswith("--icon")]
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Compact UI executable built successfully!")
        print(f"Executable location: {script_dir / 'dist' / 'PwnSafe-Compact.exe'}")
        
        # Create a simple batch file to run the executable
        batch_content = """@echo off
echo Starting PwnSafe with Compact UI...
PwnSafe-Compact.exe
pause
"""
        with open(script_dir / "dist" / "run_pwnsafe_compact.bat", "w") as f:
            f.write(batch_content)
        
        print("Created run_pwnsafe_compact.bat for easy execution")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

if __name__ == "__main__":
    print("PwnSafe Compact UI Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build the executable
    if build_compact_ui_executable():
        print("\nBuild process completed successfully!")
        print("\nFiles created:")
        print("  dist/PwnSafe-Compact.exe - Main executable with compact UI")
        print("  dist/run_pwnsafe_compact.bat - Easy run script")
        print("\nThe new compact UI features:")
        print("  • Professional desktop utility layout")
        print("  • Profile management with persistence")
        print("  • SSH key authentication support")
        print("  • Collapsible advanced settings")
        print("  • Improved keyboard navigation")
    else:
        print("\nBuild process failed!")
        sys.exit(1)
