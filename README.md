<div align="center">

# PwnSafe - Backup & Restore Utility

<img src="logo.png" alt="PwnSafe Logo" width="200" height="200">

**A Modern Hacker-Themed Backup & Restore Utility**

[![Version](https://img.shields.io/badge/version-1.4.0-blue.svg)](https://github.com/Zmk55/PwnSafe/releases)
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey.svg)](https://github.com/Zmk55/PwnSafe)

</div>

PwnSafe is a Python-based GUI utility designed to facilitate seamless backup and restore operations on remote systems. With a modern hacker-themed interface, PwnSafe simplifies the process of securely transferring files over SSH, making it ideal for managing critical data and Pwnagotchi devices.

---

## ✨ Features

### 🔧 Core Functionality
- **💾 Backup Functionality**: Create compressed backups of remote directories and securely download them to your local machine
- **📤 Restore Functionality**: Upload a backup file from your local machine and extract it on a remote system
- **🌐 Cross-Platform Compatibility**: Works on Windows, Linux, and macOS systems
- **🎨 Modern Hacker Theme**: Sleek, professional interface with dark theme styling
- **📝 Comprehensive Logging**: Detailed logs for debugging and tracking operation status

### 🤖 Pwnagotchi Integration
- **🔍 Auto-Detection**: Automatically detect and connect to Pwnagotchi devices
- **🪟 RNDIS Driver Setup**: On Windows, detect a missing RNDIS driver and offer to install the bundled driver with administrator approval
- **📸 Snapshot Detection**: Track device connections using MAC address monitoring
- **🌐 Network Configuration**: Auto-configure network settings for Pwnagotchi connectivity
- **🔗 Internet Sharing**: Enable native Windows Internet Connection Sharing from the active default-route adapter to the detected RNDIS adapter with UAC approval
- **🔄 Reconnection Monitoring**: Persistent connection tracking and automatic reconnection
- **📡 SSH Connectivity**: Query and display the connected hostname, verify Internet Sharing through `10.0.0.1`, and use an embedded interactive Paramiko terminal
- **🔑 Automatic Key Setup**: Generate and install a PwnSafe SSH key after a single password prompt when key authentication is not yet configured

### 🛠️ Advanced Features
- **🖱️ Enhanced Scrolling**: Improved mouse wheel support for better navigation
- **📱 Responsive Design**: Adaptive layout that works on different screen sizes
- **🎯 Professional UI**: Clean, modern interface with consistent theming
- **⚡ Performance Optimized**: Fast, efficient backup and restore operations

---

## 🚀 Quick Start

<div align="center">

### Download & Run
[![Download](https://img.shields.io/badge/Download-Latest%20Release-green.svg)](https://github.com/Zmk55/PwnSafe/releases/latest)

**Latest Version: v1.4.0**

</div>

1. **Download** the latest release from [GitHub Releases](https://github.com/Zmk55/PwnSafe/releases/latest)
2. **Extract** the archive to your desired location
3. **Run** the executable: `./PwnSafe` (Linux) or `PwnSafe.exe` (Windows)
4. **Connect** to your remote system or Pwnagotchi device
5. **Backup** or **Restore** your data with ease!

---

## 📋 Requirements

### Python Dependencies
- `customtkinter`
- `paramiko`

Install the required libraries using:
```bash
pip install -r requirements.txt
```

### Other Requirements
- An SSH-enabled remote system.
- A valid username and password for the remote system.

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/PwnSafe.git
   cd PwnSafe
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   venv\Scripts\activate   # On Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python pwnsafe.py
   ```

---

## Usage

1. Launch the application using the instructions above.
2. Enter the remote system's details:
   - **Host**: IP address or hostname of the remote system.
   - **Username**: SSH username.
   - **Password**: SSH password.
3. Choose the operation:
   - **Backup**:
     - Select a location to save the backup file.
     - The utility will compress specified directories on the remote system and download the backup.
   - **Restore**:
     - Select a backup file to upload.
     - The utility will upload the backup file and extract it on the remote system.
4. View logs in the output window to confirm success or troubleshoot errors.

When the Pwnagotchi is reachable and the selected credentials are complete, the
Backup, Restore, and SSH controls become available. The SSH control opens the
embedded Terminal tab using the active password or key credentials. In SSH Key
mode, PwnSafe prompts once for the device password if it needs to generate and
install a key. The visible SFTP control is currently a placeholder for a future
file-transfer interface.

### Replicate Pwnagotchi Device Repairs

The repository includes an idempotent device repair script for the fixes found
while testing PwnSafe with Pwnagotchi 2.9.5.x. It installs the missing DejaVu
oblique fonts, fixes the `enable_assoc` UI counter, and shows descriptions for
disabled plugins without loading them. It does not enable plugins or copy
credentials. Changed device files receive timestamped `.pwnsafe-*.bak` backups.

From Windows PowerShell:

```powershell
.\scripts\repair_pwnagotchi.ps1
```

The launcher defaults to `pi@10.0.0.2` and automatically uses
`%USERPROFILE%\.ssh\pwnsafe_id_rsa` when present. Use `-TargetHost`,
`-TargetUser`, `-KeyPath`, or `-NoRestart` when needed.

From Linux or macOS:

```bash
scp scripts/repair_pwnagotchi.sh pi@10.0.0.2:/tmp/
ssh -t pi@10.0.0.2 'sudo bash /tmp/repair_pwnagotchi.sh'
```

---

## Development

### Build as Executable
To package PwnSafe as a standalone executable using `PyInstaller`:
```bash
python build_windows.py
```
The executable will be located in the `dist/` folder. The Windows build script
also bundles the files in `drivers/` for automatic RNDIS setup and the native
PowerShell helper in `scripts/` for Internet Connection Sharing.

### Versioning
PwnSafe follows Semantic Versioning (`MAJOR.MINOR.PATCH`).
- Example: `v1.0.0`
- Update the version string in `__version__` in the script and tag releases in Git.

---

## Contributing

Contributions are welcome! If you'd like to improve PwnSafe:
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of changes"
   ```
4. Push your branch:
   ```bash
   git push origin feature-name
   ```
5. Submit a pull request.

---

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Changelog
See [CHANGELOG.md](CHANGELOG.md) for a detailed history of updates and features.

---

## Acknowledgments
- Built with Python and `customtkinter`.
- Inspired by the need for simplified remote backup and restore operations.

---

---

<div align="center">

## 🤝 Contact & Support

<img src="logo.png" alt="PwnSafe Logo" width="150" height="150">

**Need help or have questions?**

- 🐛 **Bug Reports**: [Open an Issue](https://github.com/Zmk55/PwnSafe/issues)
- 💡 **Feature Requests**: [Start a Discussion](https://github.com/Zmk55/PwnSafe/discussions)
- 📧 **General Questions**: [GitHub Discussions](https://github.com/Zmk55/PwnSafe/discussions)

**Made with ❤️ for the cybersecurity community**

[![GitHub](https://img.shields.io/badge/GitHub-Zmk55-black.svg)](https://github.com/Zmk55)
[![Pwnagotchi](https://img.shields.io/badge/Pwnagotchi-Community-orange.svg)](https://pwnagotchi.org)

</div>

