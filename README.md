# PwnSafe - Backup & Restore Utility

PwnSafe is a Python-based GUI utility designed to facilitate seamless backup and restore operations on remote systems. With a user-friendly interface, PwnSafe simplifies the process of securely transferring files over SSH, making it ideal for managing critical data.

---

## Features
- **Backup Functionality**: Create compressed backups of remote directories and securely download them to your local machine.
- **Restore Functionality**: Upload a backup file from your local machine and extract it on a remote system.
- **Cross-Platform Compatibility**: Works on both Windows and Linux systems.
- **User-Friendly Interface**: Built with `customtkinter` for an intuitive experience.
- **Error Logging**: Provides detailed logs for debugging and tracking the status of operations.

---

## Requirements

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

---

## Development

### Build as Executable
To package PwnSafe as a standalone executable using `PyInstaller`:
```bash
pyinstaller --onefile --windowed pwnsafe.py
```
The executable will be located in the `dist/` folder.

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

## Contact
For questions or feedback, feel free to open an issue or reach out via GitHub!

