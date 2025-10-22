# PwnSafe Build Instructions

This guide explains how to build standalone executables for PwnSafe on different platforms.

## 🚀 Quick Build

### Universal Build (Recommended)
```bash
# Build for your current platform
make build
# or
python build.py
```

### Platform-Specific Builds
```bash
# Windows
make build-windows
# or
python build_windows.py

# Linux
make build-linux
# or
python build_linux.py
```

## 📋 Prerequisites

### All Platforms
- Python 3.9 or higher
- All dependencies installed (`pip install -r requirements.txt`)

### Windows
- Windows 10/11
- PyInstaller (`pip install pyinstaller`)

### Linux
- Any modern Linux distribution
- PyInstaller (`pip install pyinstaller`)
- tkinter (usually included with Python)

### macOS
- macOS 10.14 or higher
- PyInstaller (`pip install pyinstaller`)

## 🔧 Build Process

### 1. Install Dependencies
```bash
# Install production dependencies
pip install -r requirements.txt

# Install build dependencies
pip install pyinstaller
```

### 2. Run Build Script
```bash
# Universal build (detects platform automatically)
python build.py

# Or use platform-specific scripts
python build_windows.py  # Windows
python build_linux.py    # Linux
```

### 3. Find Your Executable
After building, you'll find:
- **Windows**: `dist/PwnSafe.exe`
- **Linux**: `dist/PwnSafe`
- **macOS**: `dist/PwnSafe`

## 📦 Distribution Packages

The build scripts automatically create distribution packages:

### Windows Package
```
PwnSafe_v1.0.0_windows/
├── PwnSafe.exe
├── run_pwnsafe.bat
├── README.md
├── DEVELOPMENT.md
└── CHANGELOG.md
```

### Linux Package
```
PwnSafe_v1.0.0_linux/
├── PwnSafe
├── run_pwnsafe.sh
├── README.md
├── DEVELOPMENT.md
└── CHANGELOG.md
```

## 🎯 Features of Standalone Executables

### ✅ What's Included
- **Complete Application**: All functionality in a single file
- **No Python Required**: Runs on systems without Python installed
- **All Dependencies**: All required libraries bundled
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Modern Theme**: Professional hacker aesthetic
- **Easy Distribution**: Just copy the executable file

### 🎨 Modern Theme Features
- **Matrix Green Text**: Classic hacker terminal colors
- **Courier New Font**: Monospace font for that retro feel
- **Dark Theme**: Black backgrounds with neon accents
- **Modern Styling**: Orange and cyan accent colors
- **Terminal-Style Logs**: Timestamped messages with brackets
- **Hacker Aesthetic**: All caps labels and professional terminology

## 🚀 Running the Executable

### Windows
```cmd
# Double-click PwnSafe.exe
# Or run from command line:
PwnSafe.exe

# Or use the batch file:
run_pwnsafe.bat
```

### Linux
```bash
# Make executable (if needed)
chmod +x PwnSafe

# Run the application
./PwnSafe

# Or use the shell script:
./run_pwnsafe.sh
```

### macOS
```bash
# Run the application
./PwnSafe
```

## 🔧 Advanced Build Options

### Custom PyInstaller Options
You can modify the build scripts to add custom options:

```python
# Add custom icon
"--icon=icon.ico",

# Add version info (Windows)
"--version-file=version.txt",

# Exclude modules to reduce size
"--exclude-module=matplotlib",

# Add data files
"--add-data=config.ini:.",
```

### Building for Different Architectures

#### Windows
- **x64**: Default build (64-bit)
- **x86**: Add `--target-arch=x86` to PyInstaller command

#### Linux
- **x64**: Default build (64-bit)
- **ARM**: Build on ARM system or use cross-compilation

#### macOS
- **Intel**: Default build
- **Apple Silicon**: Build on M1/M2 Mac or use universal binary

## 🐛 Troubleshooting

### Common Issues

#### "Module not found" errors
```bash
# Add missing modules to hidden-import list
--hidden-import=missing_module
```

#### Large executable size
```bash
# Exclude unnecessary modules
--exclude-module=unused_module
```

#### GUI not showing
- Ensure you have a display server running
- Check X11 forwarding if running remotely
- Verify tkinter is properly installed

#### Permission errors (Linux/macOS)
```bash
# Make executable
chmod +x PwnSafe
```

### Build Failures

#### PyInstaller not found
```bash
pip install pyinstaller
```

#### Missing dependencies
```bash
pip install -r requirements.txt
```

#### Platform-specific issues
- **Windows**: Ensure Visual Studio Build Tools are installed
- **Linux**: Install development packages (`build-essential`)
- **macOS**: Install Xcode Command Line Tools

## 📊 Build Statistics

### Typical Executable Sizes
- **Windows**: ~50-80 MB
- **Linux**: ~40-70 MB
- **macOS**: ~45-75 MB

### Build Time
- **First build**: 2-5 minutes
- **Subsequent builds**: 30-60 seconds

## 🔄 Continuous Integration

The project includes GitHub Actions workflows that automatically build executables for all platforms when you push to the main branch.

### Manual CI Build
```bash
# Run the CI pipeline locally
make check-all
make build
```

## 📝 Notes

- Executables are built with `--onefile` for easy distribution
- The `--windowed` flag hides the console window on Windows
- All necessary dependencies are bundled automatically
- The modern theme is applied by default
- Cross-platform compatibility is maintained

## 🆘 Support

If you encounter issues building PwnSafe:

1. Check the troubleshooting section above
2. Ensure all prerequisites are installed
3. Try building with verbose output: `pyinstaller --log-level=DEBUG ...`
4. Check the GitHub Issues page for known problems
5. Create a new issue with build logs and system information
