#!/usr/bin/env python3
"""
Build script for creating Linux executable of PwnSafe.
This script creates a standalone binary that can run on Linux without Python installed.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_linux_executable():
    """Build Linux executable using PyInstaller."""
    print("🔧 Building PwnSafe for Linux...")
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # PyInstaller command for Linux
    cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--windowed",                   # Hide console window (GUI app)
        "--name=PwnSafe",               # Name of the executable
        "--icon=icon.ico",              # Icon file
        "--add-data=README.md:.",       # Include README
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
    
    try:
        # Run PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Linux executable built successfully!")
        print(f"📁 Executable location: {script_dir / 'dist' / 'PwnSafe'}")
        
        # Make the executable... executable
        executable_path = script_dir / "dist" / "PwnSafe"
        os.chmod(executable_path, 0o755)
        
        # Create a simple shell script to run the executable
        shell_script = """#!/bin/bash
echo "Starting PwnSafe..."
./PwnSafe
"""
        with open(script_dir / "dist" / "run_pwnsafe.sh", "w") as f:
            f.write(shell_script)
        os.chmod(script_dir / "dist" / "run_pwnsafe.sh", 0o755)
        
        print("📄 Created run_pwnsafe.sh for easy execution")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    return True

def create_installer_script():
    """Create a simple installer script for Linux."""
    installer_content = """#!/bin/bash
echo "========================================"
echo "   PwnSafe v1.0.0 - Cyberpunk Edition"
echo "========================================"
echo ""
echo "Installing PwnSafe..."
echo ""

# Create installation directory
INSTALL_DIR="$HOME/PwnSafe"
mkdir -p "$INSTALL_DIR"

# Copy executable
cp PwnSafe "$INSTALL_DIR/"

# Create desktop entry
DESKTOP_ENTRY="$HOME/.local/share/applications/pwnsafe.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_ENTRY" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PwnSafe
Comment=Cyberpunk Backup & Restore Utility
Exec=$INSTALL_DIR/PwnSafe
Icon=applications-system
Terminal=false
Categories=System;Utility;
EOF

# Make desktop entry executable
chmod +x "$DESKTOP_ENTRY"

# Create symlink in /usr/local/bin if user has sudo access
if command -v sudo >/dev/null 2>&1; then
    echo "Creating system-wide symlink (requires sudo)..."
    sudo ln -sf "$INSTALL_DIR/PwnSafe" /usr/local/bin/pwnsafe
fi

echo ""
echo "========================================"
echo "   Installation Complete!"
echo "========================================"
echo ""
echo "PwnSafe has been installed to:"
echo "$INSTALL_DIR/"
echo ""
echo "You can run it by:"
echo "  - Double-clicking the desktop entry"
echo "  - Running: $INSTALL_DIR/PwnSafe"
if command -v sudo >/dev/null 2>&1; then
    echo "  - Running: pwnsafe (from anywhere)"
fi
echo ""
"""
    
    with open("install_pwnsafe.sh", "w") as f:
        f.write(installer_content)
    os.chmod("install_pwnsafe.sh", 0o755)
    
    print("📄 Created install_pwnsafe.sh installer script")

def create_appimage_script():
    """Create a script to build AppImage (optional)."""
    appimage_script = """#!/bin/bash
# Optional: Build AppImage for universal Linux compatibility
# Requires: https://github.com/AppImage/AppImageKit

echo "Building AppImage (optional)..."
echo "This requires AppImageKit to be installed."

# Create AppDir structure
mkdir -p PwnSafe.AppDir/usr/bin
mkdir -p PwnSafe.AppDir/usr/share/applications
mkdir -p PwnSafe.AppDir/usr/share/icons

# Copy executable
cp dist/PwnSafe PwnSafe.AppDir/usr/bin/

# Create desktop file
cat > PwnSafe.AppDir/usr/share/applications/pwnsafe.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PwnSafe
Comment=Cyberpunk Backup & Restore Utility
Exec=pwnsafe
Icon=pwnsafe
Terminal=false
Categories=System;Utility;
EOF

# Create AppRun script
cat > PwnSafe.AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/PwnSafe" "$@"
EOF
chmod +x PwnSafe.AppDir/AppRun

echo "AppImage structure created. Use AppImageKit to build the final AppImage."
"""
    
    with open("build_appimage.sh", "w") as f:
        f.write(appimage_script)
    os.chmod("build_appimage.sh", 0o755)
    
    print("📄 Created build_appimage.sh for AppImage building")

if __name__ == "__main__":
    print("🚀 PwnSafe Linux Build Script")
    print("=" * 40)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✅ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Build the executable
    if build_linux_executable():
        create_installer_script()
        create_appimage_script()
        print("\n🎉 Build process completed successfully!")
        print("\nFiles created:")
        print("  📁 dist/PwnSafe - Main executable")
        print("  📄 dist/run_pwnsafe.sh - Easy run script")
        print("  📄 install_pwnsafe.sh - Installer script")
        print("  📄 build_appimage.sh - AppImage builder (optional)")
        print("\nTo distribute:")
        print("  1. Copy the entire 'dist' folder")
        print("  2. Or use the installer script")
        print("  3. Or build an AppImage for universal compatibility")
    else:
        print("\n❌ Build process failed!")
        sys.exit(1)
