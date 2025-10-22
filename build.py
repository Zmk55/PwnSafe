#!/usr/bin/env python3
"""
Universal build script for PwnSafe.
Automatically detects the platform and builds the appropriate executable.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def detect_platform():
    """Detect the current platform."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    else:
        return "unknown"

def build_executable():
    """Build executable for the current platform."""
    current_platform = detect_platform()
    
    print(f"🔍 Detected platform: {current_platform}")
    
    if current_platform == "windows":
        print("🪟 Building for Windows...")
        return build_windows()
    elif current_platform == "linux":
        print("🐧 Building for Linux...")
        return build_linux()
    elif current_platform == "macos":
        print("🍎 Building for macOS...")
        return build_macos()
    else:
        print(f"❌ Unsupported platform: {current_platform}")
        return False

def build_windows():
    """Build Windows executable."""
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=PwnSafe",
        "--add-data=README.md;.",
        "--hidden-import=customtkinter",
        "--hidden-import=paramiko",
        "--hidden-import=cryptography",
        "--hidden-import=bcrypt",
        "--hidden-import=PyNaCl",
        "--hidden-import=cffi",
        "--hidden-import=pycparser",
        "--hidden-import=packaging",
        "--hidden-import=darkdetect",
        "--clean",
        "pwnsafe.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Windows executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows build failed: {e}")
        return False

def build_linux():
    """Build Linux executable."""
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=PwnSafe",
        "--icon=icon.ico",
        "--add-data=README.md:.",
        "--hidden-import=customtkinter",
        "--hidden-import=paramiko",
        "--hidden-import=cryptography",
        "--hidden-import=bcrypt",
        "--hidden-import=PyNaCl",
        "--hidden-import=cffi",
        "--hidden-import=pycparser",
        "--hidden-import=packaging",
        "--hidden-import=darkdetect",
        "--clean",
        "pwnsafe.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        # Make executable
        executable_path = Path("dist/PwnSafe")
        if executable_path.exists():
            os.chmod(executable_path, 0o755)
        print("✅ Linux executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Linux build failed: {e}")
        return False

def build_macos():
    """Build macOS executable."""
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=PwnSafe",
        "--icon=icon.ico",
        "--add-data=README.md:.",
        "--hidden-import=customtkinter",
        "--hidden-import=paramiko",
        "--hidden-import=cryptography",
        "--hidden-import=bcrypt",
        "--hidden-import=PyNaCl",
        "--hidden-import=cffi",
        "--hidden-import=pycparser",
        "--hidden-import=packaging",
        "--hidden-import=darkdetect",
        "--clean",
        "pwnsafe.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ macOS executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ macOS build failed: {e}")
        return False

def create_distribution_package():
    """Create a distribution package with all necessary files."""
    current_platform = detect_platform()
    dist_dir = Path("dist")
    
    if not dist_dir.exists():
        print("❌ No dist directory found. Build first.")
        return False
    
    # Create package directory
    package_name = f"PwnSafe_v1.3.0_{current_platform}"
    package_dir = Path(package_name)
    package_dir.mkdir(exist_ok=True)
    
    # Copy executable
    if current_platform == "windows":
        exe_name = "PwnSafe.exe"
    else:
        exe_name = "PwnSafe"
    
    exe_path = dist_dir / exe_name
    if exe_path.exists():
        import shutil
        shutil.copy2(exe_path, package_dir / exe_name)
    
    # Copy documentation
    docs_to_copy = ["README.md", "DEVELOPMENT.md", "CHANGELOG.md"]
    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, package_dir / doc)
    
    # Create run script
    if current_platform == "windows":
        run_script = package_dir / "run_pwnsafe.bat"
        script_content = """@echo off
echo Starting PwnSafe...
PwnSafe.exe
pause
"""
    else:
        run_script = package_dir / "run_pwnsafe.sh"
        script_content = """#!/bin/bash
echo "Starting PwnSafe..."
./PwnSafe
"""
    
    with open(run_script, "w") as f:
        f.write(script_content)
    
    # Make script executable on Unix systems
    if current_platform != "windows":
        os.chmod(run_script, 0o755)
    
    print(f"📦 Distribution package created: {package_name}/")
    return True

def main():
    """Main build function."""
    print("🚀 PwnSafe Universal Build Script")
    print("=" * 50)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✅ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build the executable
    if build_executable():
        create_distribution_package()
        print("\n🎉 Build process completed successfully!")
        print(f"\n📁 Executable location: dist/")
        print(f"📦 Package location: PwnSafe_v1.3.0_{detect_platform()}/")
    else:
        print("\n❌ Build process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
