__version__ = "1.0.0"

import customtkinter as ctk
from tkinter import filedialog, messagebox
import paramiko
import threading
import os
import platform
import sys
from pathlib import Path


class BackupRestoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PwnSafe v1.0.0 - Cyberpunk Backup & Restore Utility")
        self.geometry("800x600")
        
        # Set dystopian hacker theme
        ctk.set_appearance_mode("dark")
        self._setup_hacker_theme()
        
        # Make window resizable
        self.minsize(700, 500)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create main container
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with cyberpunk styling
        self.header_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.header_label = ctk.CTkLabel(
            self.header_frame, 
            text="PwnSafe v1.0.0", 
            font=("Courier New", 24, "bold"),
            text_color="#00ff00"
        )
        self.header_label.pack()
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="CYBERPUNK BACKUP & RESTORE UTILITY",
            font=("Courier New", 12),
            text_color="#00ffff"
        )
        self.subtitle_label.pack()

        # Connection Section with cyberpunk styling
        self.connection_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.connection_frame.pack(fill="x", padx=20, pady=10)
        
        # Section title
        self.connection_title = ctk.CTkLabel(
            self.connection_frame,
            text="[ TARGET SYSTEM CONNECTION ]",
            font=("Courier New", 14, "bold"),
            text_color="#ff6600"
        )
        self.connection_title.grid(row=0, column=0, columnspan=3, pady=(15, 10), sticky="ew")

        # Connection inputs in a grid
        self.connection_frame.grid_columnconfigure(1, weight=1)
        
        # Host input
        host_label = ctk.CTkLabel(
            self.connection_frame, 
            text="TARGET HOST:", 
            font=("Courier New", 11, "bold"),
            text_color="#00ff00"
        )
        host_label.grid(row=1, column=0, padx=15, pady=8, sticky="w")
        
        self.host_entry = ctk.CTkEntry(
            self.connection_frame, 
            placeholder_text="192.168.1.100", 
            font=("Courier New", 11),
            placeholder_text_color="#666666"
        )
        self.host_entry.grid(row=1, column=1, padx=15, pady=8, sticky="ew")

        # Username input
        user_label = ctk.CTkLabel(
            self.connection_frame, 
            text="USERNAME:", 
            font=("Courier New", 11, "bold"),
            text_color="#00ff00"
        )
        user_label.grid(row=2, column=0, padx=15, pady=8, sticky="w")
        
        self.user_entry = ctk.CTkEntry(
            self.connection_frame, 
            placeholder_text="root", 
            font=("Courier New", 11),
            placeholder_text_color="#666666"
        )
        self.user_entry.grid(row=2, column=1, padx=15, pady=8, sticky="ew")

        # Password input
        pass_label = ctk.CTkLabel(
            self.connection_frame, 
            text="PASSWORD:", 
            font=("Courier New", 11, "bold"),
            text_color="#00ff00"
        )
        pass_label.grid(row=3, column=0, padx=15, pady=8, sticky="w")
        
        self.pass_entry = ctk.CTkEntry(
            self.connection_frame, 
            placeholder_text="••••••••", 
            show="*", 
            font=("Courier New", 11),
            placeholder_text_color="#666666"
        )
        self.pass_entry.grid(row=3, column=1, padx=15, pady=8, sticky="ew")

        # File selection section
        self.file_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.file_frame.pack(fill="x", padx=20, pady=10)
        
        file_title = ctk.CTkLabel(
            self.file_frame,
            text="[ BACKUP FILE SELECTION ]",
            font=("Courier New", 14, "bold"),
            text_color="#ff6600"
        )
        file_title.grid(row=0, column=0, columnspan=3, pady=(15, 10), sticky="ew")
        
        self.file_frame.grid_columnconfigure(1, weight=1)
        
        file_label = ctk.CTkLabel(
            self.file_frame, 
            text="BACKUP FILE:", 
            font=("Courier New", 11, "bold"),
            text_color="#00ff00"
        )
        file_label.grid(row=1, column=0, padx=15, pady=8, sticky="w")
        
        self.file_entry = ctk.CTkEntry(
            self.file_frame, 
            placeholder_text="Select .tgz backup file...", 
            font=("Courier New", 11),
            placeholder_text_color="#666666"
        )
        self.file_entry.grid(row=1, column=1, padx=15, pady=8, sticky="ew")

        self.browse_button = ctk.CTkButton(
            self.file_frame, 
            text="BROWSE", 
            command=self.browse_file,
            font=("Courier New", 11, "bold"),
            fg_color="#ff6600",
            hover_color="#ff8833"
        )
        self.browse_button.grid(row=1, column=2, padx=15, pady=8)

        # Action buttons section
        self.action_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.action_frame.pack(fill="x", padx=20, pady=10)
        
        action_title = ctk.CTkLabel(
            self.action_frame,
            text="[ SYSTEM OPERATIONS ]",
            font=("Courier New", 14, "bold"),
            text_color="#ff6600"
        )
        action_title.grid(row=0, column=0, columnspan=2, pady=(15, 10), sticky="ew")
        
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)
        
        self.backup_button = ctk.CTkButton(
            self.action_frame, 
            text="INITIATE BACKUP", 
            command=self.start_backup, 
            width=180,
            height=40,
            font=("Courier New", 12, "bold"),
            fg_color="#00ff00",
            hover_color="#00cc00",
            text_color="#000000"
        )
        self.backup_button.grid(row=1, column=0, padx=20, pady=10)

        self.restore_button = ctk.CTkButton(
            self.action_frame, 
            text="INITIATE RESTORE", 
            command=self.start_restore, 
            width=180,
            height=40,
            font=("Courier New", 12, "bold"),
            fg_color="#ff0066",
            hover_color="#cc0055",
            text_color="#ffffff"
        )
        self.restore_button.grid(row=1, column=1, padx=20, pady=10)

        # Output Log with cyberpunk styling
        self.output_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.output_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        output_title = ctk.CTkLabel(
            self.output_frame,
            text="[ SYSTEM LOG OUTPUT ]",
            font=("Courier New", 14, "bold"),
            text_color="#ff6600"
        )
        output_title.grid(row=0, column=0, pady=(15, 10), sticky="ew")
        
        self.output_frame.grid_rowconfigure(1, weight=1)
        self.output_frame.grid_columnconfigure(0, weight=1)
        
        self.output_text = ctk.CTkTextbox(
            self.output_frame, 
            corner_radius=10,
            font=("Courier New", 10),
            text_color="#00ff00",
            fg_color="#000000"
        )
        self.output_text.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        
        # Initialize with welcome message
        self.log_message(">>> PwnSafe v1.0.0 - Cyberpunk Backup & Restore Utility <<<")
        self.log_message(">>> System initialized. Ready for operations. <<<")
        self.log_message(">>> Target system connection required. <<<")

    def _setup_hacker_theme(self):
        """Setup the cyberpunk hacker theme colors and styling."""
        # Custom color scheme for cyberpunk theme
        self.hacker_colors = {
            'primary': '#00ff00',      # Matrix green
            'secondary': '#00ffff',    # Cyan
            'accent': '#ff6600',       # Orange
            'danger': '#ff0066',       # Pink/Red
            'warning': '#ffff00',      # Yellow
            'background': '#000000',   # Black
            'surface': '#111111',      # Dark gray
            'text': '#00ff00',         # Green text
            'muted': '#666666'         # Gray
        }

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Backup Files", "*.tgz")])
        if filename:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filename)

    def log_message(self, message, level="INFO"):
        """Log messages with cyberpunk styling."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on message level
        color_map = {
            "INFO": "#00ff00",      # Green
            "SUCCESS": "#00ffff",   # Cyan
            "WARNING": "#ffff00",   # Yellow
            "ERROR": "#ff0066",     # Pink/Red
            "SYSTEM": "#ff6600"     # Orange
        }
        
        # Format message with cyberpunk styling
        if level == "ERROR":
            formatted_msg = f"[{timestamp}] >>> ERROR: {message} <<<\n"
        elif level == "SUCCESS":
            formatted_msg = f"[{timestamp}] >>> SUCCESS: {message} <<<\n"
        elif level == "WARNING":
            formatted_msg = f"[{timestamp}] >>> WARNING: {message} <<<\n"
        elif level == "SYSTEM":
            formatted_msg = f"[{timestamp}] >>> SYSTEM: {message} <<<\n"
        else:
            formatted_msg = f"[{timestamp}] >>> {message} <<<\n"
        
        self.output_text.insert("end", formatted_msg)
        self.output_text.see("end")

    def ssh_connect(self):
        host = self.host_entry.get()
        username = self.user_entry.get()
        password = self.pass_entry.get()

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=username, password=password)
            return ssh
        except Exception as e:
            self.log_message(f"SSH Connection Failed: {e}", "ERROR")
            return None

    def start_backup(self):
        threading.Thread(target=self.backup, daemon=True).start()

    def backup(self):
        ssh = self.ssh_connect()
        if not ssh:
            return  # Connection failed

        self.log_message("Initiating backup sequence...", "SYSTEM")

        # Ask the user where to save the backup file locally
        save_path = filedialog.asksaveasfilename(
            defaultextension=".tgz", filetypes=[("TGZ Files", "*.tgz")]
        )
        if not save_path:
            self.log_message("Backup canceled: No save location selected.", "ERROR")
            ssh.close()
            return

        # This command sends tar output to stdout, then we compress it with gzip
        # so we can capture the entire thing locally, just like your old batch file.
        command = (
            "sudo tar --exclude='/etc/pwnagotchi/log/*.log' "
            "--warning=none -cf - "
            "/etc/pwnagotchi/ /root/.ssh /home/pi/handshakes "
            "| gzip -9"
        )

        stdin, stdout, stderr = ssh.exec_command(command)

        try:
            # 1) Stream the tar+gzip data to the local file
            with open(save_path, "wb") as f:
                while True:
                    chunk = stdout.read(4096)
                    if not chunk:
                        break
                    f.write(chunk)

            # 2) Read any stderr lines (warnings or errors)
            errors = stderr.read().decode().strip()

            # 3) Check the exit code of the command
            exit_code = stdout.channel.recv_exit_status()

            # 4) Decide if we succeeded or failed
            if exit_code == 0:
                # tar returned success
                if errors:
                    # Some warnings (e.g., "Removing leading '/'") - not fatal
                    for line in errors.splitlines():
                        self.log_message(f"{line}", "WARNING")

                self.log_message(f"Backup successfully saved to: {save_path}", "SUCCESS")
            else:
                # Non-zero exit code => real error
                self.log_message(f"tar failed with exit code {exit_code}", "ERROR")
                if errors:
                    self.log_message(errors, "ERROR")

        except Exception as e:
            self.log_message(f"Failed to download backup stream: {e}", "ERROR")
        finally:
            ssh.close()

    def start_restore(self):
        threading.Thread(target=self.restore, daemon=True).start()

    def restore(self):
        ssh = self.ssh_connect()
        if not ssh:
            return  # Connection failed

        backup_file = self.file_entry.get()
        if not backup_file:
            self.log_message("No backup file selected!", "ERROR")
            ssh.close()
            return

        self.log_message(f"Uploading {backup_file}...", "SYSTEM")
        try:
            sftp = ssh.open_sftp()
            sftp.put(backup_file, "/tmp/restore.tgz")
            sftp.close()
            self.log_message("File uploaded successfully.", "SUCCESS")
        except Exception as e:
            self.log_message(f"Failed to upload file: {e}", "ERROR")
            ssh.close()
            return

        self.log_message("Restoring backup on remote device...", "SYSTEM")
        command = "sudo tar -xzvf /tmp/restore.tgz -C /"
        stdin, stdout, stderr = ssh.exec_command(command)
        errors = stderr.read().decode().strip()
        output = stdout.read().decode()

        # Check exit code to see if restore succeeded
        exit_code = stdout.channel.recv_exit_status()
        if exit_code == 0:
            # Success
            if errors:
                # Could be warnings
                self.log_message(f"{errors}", "WARNING")
            self.log_message(f"Restore Output: {output}")
            self.log_message("Restore completed successfully!", "SUCCESS")
        else:
            # Failure
            self.log_message(f"tar restore failed with exit code {exit_code}", "ERROR")
            if errors:
                self.log_message(errors, "ERROR")

        ssh.close()

    def detect_platform(self):
        """Detect the current operating system and log it."""
        current_platform = platform.system().lower()
        self.log_message(f"Running on {current_platform.capitalize()} system.", "SYSTEM")
        return current_platform
    
    def get_resource_path(self, relative_path):
        """Get the absolute path to a resource, works for dev and for PyInstaller."""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    try:
        # Initialize the application
        app = BackupRestoreApp()
        
        # Detect and log platform
        app.detect_platform()
        
        # Start the main loop
        app.mainloop()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
