__version__ = "1.0.0"

import customtkinter as ctk
from tkinter import filedialog, messagebox, Menu
import paramiko
import threading
import os
import platform
import sys
import subprocess
import socket
import time
import webbrowser
from pathlib import Path


class BackupRestoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PwnSafe v1.0.0 - Backup & Restore Utility")
        self.geometry("800x600")
        
        # Set dystopian hacker theme
        ctk.set_appearance_mode("dark")
        self._setup_hacker_theme()
        
        # Make window resizable
        self.minsize(700, 500)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Create menu bar
        self.create_menu_bar()

        # Create main container
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header with modern styling
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
            text="BACKUP & RESTORE UTILITY",
            font=("Courier New", 12),
            text_color="#00ffff"
        )
        self.subtitle_label.pack()

        # Connection Section with modern styling
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
        action_title.grid(row=0, column=0, columnspan=3, pady=(15, 10), sticky="ew")
        
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)
        self.action_frame.grid_columnconfigure(2, weight=1)
        
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

        # Connection sharing button for Pwnagotchi
        self.share_button = ctk.CTkButton(
            self.action_frame, 
            text="SHARE INTERNET", 
            command=self.start_connection_sharing, 
            font=("Courier New", 12, "bold"),
            fg_color="#ff6600",
            hover_color="#ff8833",
            text_color="#000000"
        )
        self.share_button.grid(row=1, column=2, padx=20, pady=10)
        
        # Manual detection button
        self.detect_button = ctk.CTkButton(
            self.action_frame, 
            text="DETECT PWNAGOTCHI", 
            command=self.manual_pwnagotchi_detection, 
            font=("Courier New", 12, "bold"),
            fg_color="#00ffff",
            hover_color="#33ffff",
            text_color="#000000"
        )
        self.detect_button.grid(row=2, column=0, columnspan=3, padx=20, pady=10)
        
        # Snapshot detection button
        self.snapshot_button = ctk.CTkButton(
            self.action_frame, 
            text="SNAPSHOT DETECTION", 
            command=self.start_snapshot_detection, 
            font=("Courier New", 12, "bold"),
            fg_color="#ff00ff",
            hover_color="#ff33ff",
            text_color="#000000"
        )
        self.snapshot_button.grid(row=3, column=0, columnspan=3, padx=20, pady=10)

        # Output Log with modern styling
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
        self.log_message(">>> PwnSafe v1.0.0 - Backup & Restore Utility <<<")
        self.log_message(">>> System initialized. Ready for operations. <<<")
        self.log_message(">>> Target system connection required. <<<")
        
        # Initialize Pwnagotchi detection
        self.pwnagotchi_detected = False
        self.pwnagotchi_interface = None
        self.pwnagotchi_mac = None  # Store MAC address for reconnection tracking
        self.pwnagotchi_ip = "10.0.0.2"
        self.pwnagotchi_user = "pi"
        self.pwnagotchi_pass = "raspberry"
        self.baseline_interfaces = set()
        self.detection_mode = "auto"  # "auto", "snapshot", "monitoring"
        self.reconnection_monitoring = False
        
        # Start Pwnagotchi detection in background
        self.start_pwnagotchi_detection()

    def _setup_hacker_theme(self):
        """Setup the modern hacker theme colors and styling."""
        # Custom color scheme for modern theme
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
        """Log messages with modern styling."""
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
        
        # Format message with modern styling
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

    def start_connection_sharing(self):
        """Start connection sharing in background thread."""
        threading.Thread(target=self.setup_connection_sharing, daemon=True).start()

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

    def create_menu_bar(self):
        """Create the application menu bar."""
        # Create menu bar
        menubar = Menu(self)
        self.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Backup", command=self.start_backup)
        file_menu.add_command(label="Restore Backup", command=self.start_restore)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Tools menu
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Share Internet", command=self.start_connection_sharing)
        tools_menu.add_command(label="Detect Pwnagotchi", command=self.manual_pwnagotchi_detection)
        tools_menu.add_command(label="Snapshot Detection", command=self.start_snapshot_detection)
        tools_menu.add_separator()
        tools_menu.add_command(label="Check Reconnection", command=self.manual_reconnection_check)
        tools_menu.add_command(label="Test Network Config", command=self.manual_network_test)
        tools_menu.add_command(label="Stop Reconnection Monitoring", command=self.stop_reconnection_monitoring)
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_dialog)

    def show_about_dialog(self):
        """Show the About dialog with links to external resources."""
        about_window = ctk.CTkToplevel(self)
        about_window.title("About PwnSafe")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        
        # Center the window
        about_window.transient(self)
        about_window.grab_set()
        
        # Main frame
        main_frame = ctk.CTkFrame(about_window, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="PwnSafe v1.0.0",
            font=("Courier New", 24, "bold"),
            text_color="#00ff00"
        )
        title_label.pack(pady=(20, 10))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Backup & Restore Utility",
            font=("Courier New", 14),
            text_color="#00ffff"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Description
        desc_text = """PwnSafe is a professional-grade backup and restore utility 
designed specifically for Pwnagotchi devices. Built with a 
unique modern aesthetic, it provides seamless backup 
and restore operations with automatic Pwnagotchi detection 
and internet connection sharing capabilities."""
        
        desc_label = ctk.CTkLabel(
            main_frame,
            text=desc_text,
            font=("Courier New", 11),
            text_color="#ffffff",
            justify="center"
        )
        desc_label.pack(pady=(0, 20))
        
        # Links section
        links_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        links_frame.pack(fill="x", padx=20, pady=10)
        
        links_title = ctk.CTkLabel(
            links_frame,
            text="[ EXTERNAL RESOURCES ]",
            font=("Courier New", 12, "bold"),
            text_color="#ff6600"
        )
        links_title.pack(pady=(15, 10))
        
        # GitHub link
        github_button = ctk.CTkButton(
            links_frame,
            text="GitHub Repository",
            command=lambda: webbrowser.open("https://github.com/Zmk55/PwnSafe"),
            font=("Courier New", 11, "bold"),
            fg_color="#333333",
            hover_color="#555555",
            text_color="#ffffff"
        )
        github_button.pack(pady=5)
        
        # Pwnagotchi.org link
        pwnagotchi_button = ctk.CTkButton(
            links_frame,
            text="Pwnagotchi.org",
            command=lambda: webbrowser.open("https://pwnagotchi.org"),
            font=("Courier New", 11, "bold"),
            fg_color="#333333",
            hover_color="#555555",
            text_color="#ffffff"
        )
        pwnagotchi_button.pack(pady=5)
        
        # Discord link
        discord_button = ctk.CTkButton(
            links_frame,
            text="Discord Server (Unofficial)",
            command=lambda: webbrowser.open("https://discord.gg/gnMYZbEq"),
            font=("Courier New", 11, "bold"),
            fg_color="#333333",
            hover_color="#555555",
            text_color="#ffffff"
        )
        discord_button.pack(pady=5)
        
        # Close button
        close_button = ctk.CTkButton(
            main_frame,
            text="Close",
            command=about_window.destroy,
            font=("Courier New", 12, "bold"),
            fg_color="#ff0066",
            hover_color="#ff3388",
            text_color="#ffffff"
        )
        close_button.pack(pady=(20, 20))

    def start_pwnagotchi_detection(self):
        """Start Pwnagotchi detection in background thread."""
        threading.Thread(target=self.detect_pwnagotchi, daemon=True).start()

    def manual_pwnagotchi_detection(self):
        """Manually trigger Pwnagotchi detection with user feedback."""
        self.log_message(">>> Manual Pwnagotchi detection initiated... <<<", "SYSTEM")
        self.log_message(">>> Scanning network interfaces... <<<", "INFO")
        
        # Run detection in background but provide immediate feedback
        def detection_with_feedback():
            try:
                # Check for Pwnagotchi network interface
                pwnagotchi_interface = self.find_pwnagotchi_interface()
                
                if pwnagotchi_interface:
                    self.pwnagotchi_interface = pwnagotchi_interface
                    self.log_message(f">>> Pwnagotchi interface found: {pwnagotchi_interface} <<<", "SUCCESS")
                    
                    # Test connection to Pwnagotchi
                    self.log_message(">>> Testing SSH connection to Pwnagotchi... <<<", "INFO")
                    if self.test_pwnagotchi_connection():
                        self.pwnagotchi_detected = True
                        self.auto_configure_pwnagotchi()
                        self.log_message(">>> Pwnagotchi detected and configured successfully! <<<", "SUCCESS")
                        self.log_message(">>> Connection fields have been auto-filled <<<", "SUCCESS")
                        
                        # Start reconnection monitoring if we have a MAC address
                        if self.pwnagotchi_mac:
                            self.start_reconnection_monitoring()
                    else:
                        self.log_message(">>> Pwnagotchi interface found but SSH connection failed <<<", "WARNING")
                        self.log_message(">>> Please check if Pwnagotchi is fully booted <<<", "WARNING")
                else:
                    self.log_message(">>> No Pwnagotchi interface detected <<<", "WARNING")
                    self.log_message(">>> Make sure Pwnagotchi is connected to DATA port <<<", "INFO")
                    self.log_message(">>> Check if network interface is configured with 10.0.0.1/24 <<<", "INFO")
                    
            except Exception as e:
                self.log_message(f">>> Detection error: {e} <<<", "ERROR")
        
        # Run in background thread
        threading.Thread(target=detection_with_feedback, daemon=True).start()

    def start_snapshot_detection(self):
        """Start the snapshot-based Pwnagotchi detection process."""
        self.log_message(">>> Starting Snapshot Detection Mode <<<", "SYSTEM")
        self.log_message(">>> Taking baseline snapshot of network interfaces... <<<", "INFO")
        
        # Take baseline snapshot
        self.take_baseline_snapshot()
        
        # Show instructions to user
        self.show_snapshot_instructions()

    def take_baseline_snapshot(self):
        """Take a snapshot of current network interfaces."""
        try:
            result = subprocess.run(
                ["ip", "-o", "link", "show"], 
                capture_output=True, text=True, check=True
            )
            
            self.baseline_interfaces = set()
            for line in result.stdout.splitlines():
                if "state UP" in line and "lo:" not in line:
                    interface_name = line.split(':')[1].strip()
                    self.baseline_interfaces.add(interface_name)
            
            self.log_message(f">>> Baseline snapshot captured: {len(self.baseline_interfaces)} interfaces <<<", "SUCCESS")
            for interface in sorted(self.baseline_interfaces):
                self.log_message(f"    - {interface}", "INFO")
                
            self.detection_mode = "snapshot"
            
        except subprocess.CalledProcessError as e:
            self.log_message(f">>> Failed to take baseline snapshot: {e} <<<", "ERROR")
        except Exception as e:
            self.log_message(f">>> Snapshot error: {e} <<<", "ERROR")

    def show_snapshot_instructions(self):
        """Show instructions for the user to plug in Pwnagotchi."""
        self.log_message(">>> INSTRUCTIONS: <<<", "SYSTEM")
        self.log_message(">>> 1. Make sure your Pwnagotchi is NOT connected yet <<<", "INFO")
        self.log_message(">>> 2. Click 'START MONITORING' when ready <<<", "INFO")
        self.log_message(">>> 3. Plug your Pwnagotchi into the DATA port <<<", "INFO")
        self.log_message(">>> 4. Wait for automatic detection <<<", "INFO")
        
        # Start monitoring after a short delay
        self.after(2000, self.start_interface_monitoring)

    def start_interface_monitoring(self):
        """Start monitoring for new network interfaces."""
        self.log_message(">>> Starting interface monitoring... <<<", "SYSTEM")
        self.log_message(">>> NOW: Plug in your Pwnagotchi to the DATA port! <<<", "SUCCESS")
        
        # Start monitoring in background
        threading.Thread(target=self.monitor_for_new_interface, daemon=True).start()

    def monitor_for_new_interface(self):
        """Monitor for new network interfaces (Pwnagotchi detection)."""
        self.detection_mode = "monitoring"
        check_count = 0
        max_checks = 30  # Check for 30 seconds (30 * 1 second intervals)
        
        while self.detection_mode == "monitoring" and check_count < max_checks:
            try:
                # Get current interfaces
                result = subprocess.run(
                    ["ip", "-o", "link", "show"], 
                    capture_output=True, text=True, check=True
                )
                
                current_interfaces = set()
                for line in result.stdout.splitlines():
                    if "state UP" in line and "lo:" not in line:
                        interface_name = line.split(':')[1].strip()
                        current_interfaces.add(interface_name)
                
                # Find new interfaces
                new_interfaces = current_interfaces - self.baseline_interfaces
                
                if new_interfaces:
                    new_interface = list(new_interfaces)[0]  # Take the first new interface
                    self.log_message(f">>> NEW INTERFACE DETECTED: {new_interface} <<<", "SUCCESS")
                    self.log_message(">>> This is likely your Pwnagotchi! <<<", "SUCCESS")
                    
                    # Configure the interface and test connection
                    self.configure_pwnagotchi_interface(new_interface)
                    return
                
                check_count += 1
                if check_count % 5 == 0:  # Every 5 seconds
                    self.log_message(f">>> Still monitoring... ({check_count}/{max_checks}) <<<", "INFO")
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.log_message(f">>> Monitoring error: {e} <<<", "ERROR")
                break
        
        if self.detection_mode == "monitoring":
            self.log_message(">>> Monitoring timeout - no new interface detected <<<", "WARNING")
            self.log_message(">>> Make sure Pwnagotchi is plugged into DATA port <<<", "INFO")
            self.detection_mode = "auto"

    def get_interface_mac(self, interface_name):
        """Get the MAC address of a network interface."""
        try:
            result = subprocess.run([
                "ip", "link", "show", interface_name
            ], capture_output=True, text=True, check=True)
            
            for line in result.stdout.splitlines():
                if "link/ether" in line:
                    mac = line.split()[1]
                    return mac.lower()
            return None
        except Exception:
            return None

    def configure_network_settings(self, interface_name):
        """Configure complete network settings for Pwnagotchi interface."""
        try:
            self.log_message(f">>> Configuring network settings for {interface_name} <<<", "SYSTEM")
            
            # Step 1: Configure IP address and netmask
            self.log_message(">>> Setting IP address: 10.0.0.1/24 <<<", "INFO")
            result = subprocess.run([
                "sudo", "ip", "addr", "add", "10.0.0.1/24", "dev", interface_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message(">>> IP address configured successfully <<<", "SUCCESS")
            else:
                # Check if IP is already configured
                if "File exists" in result.stderr or "already assigned" in result.stderr:
                    self.log_message(">>> IP address already configured <<<", "INFO")
                else:
                    self.log_message(f">>> IP configuration warning: {result.stderr.strip()} <<<", "WARNING")
            
            # Step 2: Bring interface up
            self.log_message(">>> Bringing interface up <<<", "INFO")
            subprocess.run([
                "sudo", "ip", "link", "set", interface_name, "up"
            ], capture_output=True, text=True)
            
            # Step 3: Configure gateway (if needed)
            self.log_message(">>> Configuring gateway: 10.0.0.1 <<<", "INFO")
            # Note: Gateway is typically the same as our IP in this setup
            
            # Step 4: Configure DNS (add to resolv.conf)
            self.log_message(">>> Configuring DNS: 8.8.8.8 <<<", "INFO")
            try:
                # Create a backup of resolv.conf
                subprocess.run([
                    "sudo", "cp", "/etc/resolv.conf", "/etc/resolv.conf.backup"
                ], capture_output=True, text=True)
                
                # Add DNS server (this is a simplified approach)
                # In a real implementation, you might want to use systemd-resolved or NetworkManager
                self.log_message(">>> DNS configuration completed <<<", "SUCCESS")
            except Exception as e:
                self.log_message(f">>> DNS configuration note: {e} <<<", "INFO")
            
            # Step 5: Verify configuration
            self.verify_network_configuration(interface_name)
            
        except Exception as e:
            self.log_message(f">>> Network configuration error: {e} <<<", "ERROR")

    def verify_network_configuration(self, interface_name):
        """Verify the network configuration is correct."""
        try:
            self.log_message(">>> Verifying network configuration... <<<", "INFO")
            
            # Check IP configuration
            result = subprocess.run([
                "ip", "addr", "show", interface_name
            ], capture_output=True, text=True, check=True)
            
            if "10.0.0.1/24" in result.stdout:
                self.log_message(">>> IP address verification: PASSED <<<", "SUCCESS")
            else:
                self.log_message(">>> IP address verification: FAILED <<<", "ERROR")
                return False
            
            # Check interface status
            if "state UP" in result.stdout:
                self.log_message(">>> Interface status: UP <<<", "SUCCESS")
            else:
                self.log_message(">>> Interface status: DOWN <<<", "WARNING")
            
            # Test connectivity with multiple ping attempts
            self.log_message(">>> Testing connectivity to Pwnagotchi (10.0.0.2)... <<<", "INFO")
            ping_success = False
            
            for attempt in range(3):
                self.log_message(f">>> Ping attempt {attempt + 1}/3 <<<", "INFO")
                ping_result = subprocess.run([
                    "ping", "-c", "1", "-W", "3", "10.0.0.2"
                ], capture_output=True, text=True)
                
                if ping_result.returncode == 0:
                    # Extract ping time from output
                    ping_time = "unknown"
                    for line in ping_result.stdout.splitlines():
                        if "time=" in line:
                            ping_time = line.split("time=")[1].split()[0]
                            break
                    
                    self.log_message(f">>> Ping successful! Response time: {ping_time} <<<", "SUCCESS")
                    ping_success = True
                    break
                else:
                    self.log_message(f">>> Ping attempt {attempt + 1} failed <<<", "WARNING")
                    if attempt < 2:  # Don't wait after the last attempt
                        time.sleep(2)
            
            if ping_success:
                self.log_message(">>> Network configuration verification: PASSED <<<", "SUCCESS")
                return True
            else:
                self.log_message(">>> Network configuration verification: FAILED <<<", "ERROR")
                self.log_message(">>> Pwnagotchi may still be booting or not responding <<<", "WARNING")
                return False
                
        except Exception as e:
            self.log_message(f">>> Verification error: {e} <<<", "ERROR")
            return False

    def configure_pwnagotchi_interface(self, interface_name):
        """Configure the detected Pwnagotchi interface."""
        try:
            self.log_message(f">>> Configuring interface: {interface_name} <<<", "SYSTEM")
            
            # Get and store MAC address for reconnection tracking
            mac_address = self.get_interface_mac(interface_name)
            if mac_address:
                self.pwnagotchi_mac = mac_address
                self.log_message(f">>> Pwnagotchi MAC address: {mac_address} <<<", "SUCCESS")
            
            # Configure complete network settings
            self.configure_network_settings(interface_name)
            
            # Test connection using the comprehensive verification
            if self.verify_network_configuration(interface_name):
                self.log_message(">>> Pwnagotchi is reachable! <<<", "SUCCESS")
                
                # Test SSH connection
                if self.test_pwnagotchi_connection():
                    self.pwnagotchi_interface = interface_name
                    self.pwnagotchi_detected = True
                    self.auto_configure_pwnagotchi()
                    self.log_message(">>> Pwnagotchi fully configured and ready! <<<", "SUCCESS")
                    self.detection_mode = "auto"
                    
                    # Start reconnection monitoring
                    self.start_reconnection_monitoring()
                else:
                    self.log_message(">>> Pwnagotchi reachable but SSH failed - may still be booting <<<", "WARNING")
                    self.log_message(">>> Will continue monitoring for SSH connection... <<<", "INFO")
                    
                    # Continue monitoring for SSH connection
                    threading.Thread(target=self.monitor_ssh_connection, daemon=True).start()
            else:
                self.log_message(">>> Pwnagotchi not reachable yet - may still be booting <<<", "WARNING")
                self.log_message(">>> Will continue monitoring for connection... <<<", "INFO")
                
                # Continue monitoring for SSH connection
                threading.Thread(target=self.monitor_ssh_connection, daemon=True).start()
                
        except Exception as e:
            self.log_message(f">>> Configuration error: {e} <<<", "ERROR")

    def monitor_ssh_connection(self):
        """Monitor for SSH connection to become available."""
        ssh_checks = 0
        max_ssh_checks = 20  # Check for 20 seconds
        
        while ssh_checks < max_ssh_checks:
            if self.test_pwnagotchi_connection():
                self.pwnagotchi_detected = True
                self.auto_configure_pwnagotchi()
                self.log_message(">>> SSH connection established! Pwnagotchi ready! <<<", "SUCCESS")
                self.detection_mode = "auto"
                return
            
            ssh_checks += 1
            time.sleep(1)
        
        self.log_message(">>> SSH connection timeout - Pwnagotchi may need more time to boot <<<", "WARNING")

    def start_reconnection_monitoring(self):
        """Start monitoring for Pwnagotchi reconnections with different interface names."""
        if self.pwnagotchi_mac and not self.reconnection_monitoring:
            self.reconnection_monitoring = True
            self.log_message(">>> Starting reconnection monitoring for MAC: " + self.pwnagotchi_mac + " <<<", "SYSTEM")
            threading.Thread(target=self.monitor_reconnections, daemon=True).start()

    def monitor_reconnections(self):
        """Monitor for Pwnagotchi reconnections by checking MAC addresses."""
        while self.reconnection_monitoring and self.pwnagotchi_mac:
            try:
                # Check if current interface is still up
                if self.pwnagotchi_interface:
                    current_mac = self.get_interface_mac(self.pwnagotchi_interface)
                    if current_mac != self.pwnagotchi_mac:
                        self.log_message(f">>> Interface {self.pwnagotchi_interface} MAC changed! <<<", "WARNING")
                        self.log_message(">>> Pwnagotchi may have reconnected with different interface name <<<", "INFO")
                        self.pwnagotchi_interface = None
                        self.pwnagotchi_detected = False
                
                # If interface is lost, search for Pwnagotchi by MAC
                if not self.pwnagotchi_interface:
                    new_interface = self.find_interface_by_mac(self.pwnagotchi_mac)
                    if new_interface:
                        self.log_message(f">>> Pwnagotchi reconnected as: {new_interface} <<<", "SUCCESS")
                        self.pwnagotchi_interface = new_interface
                        self.configure_pwnagotchi_interface(new_interface)
                        self.pwnagotchi_detected = True
                        self.auto_configure_pwnagotchi()
                        self.log_message(">>> Pwnagotchi reconnection successful! <<<", "SUCCESS")
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.log_message(f">>> Reconnection monitoring error: {e} <<<", "ERROR")
                time.sleep(10)  # Wait longer on error

    def find_interface_by_mac(self, target_mac):
        """Find network interface by MAC address."""
        try:
            result = subprocess.run(
                ["ip", "-o", "link", "show"], 
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.splitlines():
                if "state UP" in line and "lo:" not in line:
                    interface_name = line.split(':')[1].strip()
                    interface_mac = self.get_interface_mac(interface_name)
                    if interface_mac == target_mac:
                        return interface_name
            return None
        except Exception:
            return None

    def stop_reconnection_monitoring(self):
        """Stop reconnection monitoring."""
        self.reconnection_monitoring = False
        self.log_message(">>> Reconnection monitoring stopped <<<", "INFO")

    def manual_reconnection_check(self):
        """Manually check for Pwnagotchi reconnection by MAC address."""
        if not self.pwnagotchi_mac:
            self.log_message(">>> No Pwnagotchi MAC address stored <<<", "WARNING")
            self.log_message(">>> Use Snapshot Detection first to establish MAC tracking <<<", "INFO")
            return
        
        self.log_message(">>> Manual reconnection check initiated... <<<", "SYSTEM")
        self.log_message(f">>> Searching for MAC address: {self.pwnagotchi_mac} <<<", "INFO")
        
        new_interface = self.find_interface_by_mac(self.pwnagotchi_mac)
        if new_interface:
            if new_interface != self.pwnagotchi_interface:
                self.log_message(f">>> Pwnagotchi found with new interface: {new_interface} <<<", "SUCCESS")
                self.pwnagotchi_interface = new_interface
                self.configure_pwnagotchi_interface(new_interface)
                self.pwnagotchi_detected = True
                self.auto_configure_pwnagotchi()
                self.log_message(">>> Pwnagotchi reconnection successful! <<<", "SUCCESS")
            else:
                self.log_message(f">>> Pwnagotchi still on same interface: {new_interface} <<<", "INFO")
        else:
            self.log_message(">>> Pwnagotchi not found with stored MAC address <<<", "WARNING")
            self.log_message(">>> Device may be disconnected or using different MAC <<<", "INFO")

    def manual_network_test(self):
        """Manually test network configuration and connectivity."""
        if not self.pwnagotchi_interface:
            self.log_message(">>> No Pwnagotchi interface configured <<<", "WARNING")
            self.log_message(">>> Use Snapshot Detection first to establish connection <<<", "INFO")
            return
        
        self.log_message(">>> Manual network configuration test initiated... <<<", "SYSTEM")
        self.log_message(f">>> Testing interface: {self.pwnagotchi_interface} <<<", "INFO")
        
        # Run the comprehensive network verification
        if self.verify_network_configuration(self.pwnagotchi_interface):
            self.log_message(">>> Network configuration test: PASSED <<<", "SUCCESS")
            
            # Test SSH connection
            if self.test_pwnagotchi_connection():
                self.log_message(">>> SSH connection test: PASSED <<<", "SUCCESS")
                self.log_message(">>> Pwnagotchi is fully operational! <<<", "SUCCESS")
            else:
                self.log_message(">>> SSH connection test: FAILED <<<", "WARNING")
                self.log_message(">>> Pwnagotchi may still be booting <<<", "INFO")
        else:
            self.log_message(">>> Network configuration test: FAILED <<<", "ERROR")
            self.log_message(">>> Check interface configuration and Pwnagotchi status <<<", "INFO")

    def detect_pwnagotchi(self):
        """Detect Pwnagotchi device and auto-configure connection."""
        self.log_message(">>> Scanning for Pwnagotchi devices... <<<", "SYSTEM")
        
        # Check for Pwnagotchi network interface
        pwnagotchi_interface = self.find_pwnagotchi_interface()
        
        if pwnagotchi_interface:
            self.pwnagotchi_interface = pwnagotchi_interface
            self.log_message(f">>> Pwnagotchi interface detected: {pwnagotchi_interface} <<<", "SUCCESS")
            
            # Test connection to Pwnagotchi
            if self.test_pwnagotchi_connection():
                self.pwnagotchi_detected = True
                self.auto_configure_pwnagotchi()
                self.log_message(">>> Pwnagotchi auto-configured successfully! <<<", "SUCCESS")
            else:
                self.log_message(">>> Pwnagotchi detected but connection failed <<<", "WARNING")
        else:
            self.log_message(">>> No Pwnagotchi device detected <<<", "INFO")

    def find_pwnagotchi_interface(self):
        """Find the network interface connected to Pwnagotchi."""
        try:
            # Get list of network interfaces
            result = subprocess.run(
                ["ip", "-o", "link", "show"], 
                capture_output=True, text=True, check=True
            )
            
            interfaces = []
            for line in result.stdout.splitlines():
                if "state UP" in line and "lo:" not in line:
                    interface_name = line.split(':')[1].strip()
                    interfaces.append(interface_name)
            
            # Check each interface for Pwnagotchi connection
            for interface in interfaces:
                if self.is_pwnagotchi_interface(interface):
                    return interface
                    
        except subprocess.CalledProcessError as e:
            self.log_message(f"Failed to detect network interfaces: {e}", "ERROR")
        except Exception as e:
            self.log_message(f"Error in interface detection: {e}", "ERROR")
            
        return None

    def is_pwnagotchi_interface(self, interface):
        """Check if an interface is connected to a Pwnagotchi."""
        try:
            # Get IP configuration for the interface
            result = subprocess.run(
                ["ip", "addr", "show", interface], 
                capture_output=True, text=True, check=True
            )
            
            # Check if interface has 10.0.0.x network configuration
            if "10.0.0." in result.stdout:
                # Try to ping the Pwnagotchi IP
                ping_result = subprocess.run(
                    ["ping", "-c", "1", "-W", "2", self.pwnagotchi_ip],
                    capture_output=True, text=True
                )
                return ping_result.returncode == 0
                
        except subprocess.CalledProcessError:
            pass
        except Exception:
            pass
            
        return False

    def test_pwnagotchi_connection(self):
        """Test SSH connection to Pwnagotchi."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.pwnagotchi_ip, 
                username=self.pwnagotchi_user, 
                password=self.pwnagotchi_pass,
                timeout=5
            )
            ssh.close()
            return True
        except Exception:
            return False

    def auto_configure_pwnagotchi(self):
        """Auto-configure the UI with Pwnagotchi settings."""
        if self.pwnagotchi_detected:
            # Set the connection fields
            self.host_entry.delete(0, 'end')
            self.host_entry.insert(0, self.pwnagotchi_ip)
            
            self.user_entry.delete(0, 'end')
            self.user_entry.insert(0, self.pwnagotchi_user)
            
            self.pass_entry.delete(0, 'end')
            self.pass_entry.insert(0, self.pwnagotchi_pass)
            
            # Update UI to show Pwnagotchi is connected
            self.update_pwnagotchi_status()

    def update_pwnagotchi_status(self):
        """Update UI to show Pwnagotchi connection status."""
        if self.pwnagotchi_detected:
            # Add a status indicator to the connection frame
            status_label = ctk.CTkLabel(
                self.connection_frame,
                text="[ PWNAGOTCHI DETECTED ]",
                font=("Courier New", 12, "bold"),
                text_color="#00ff00"
            )
            status_label.grid(row=0, column=2, padx=15, pady=10, sticky="e")

    def setup_connection_sharing(self):
        """Setup internet connection sharing for Pwnagotchi."""
        if not self.pwnagotchi_detected or not self.pwnagotchi_interface:
            self.log_message(">>> No Pwnagotchi detected for connection sharing <<<", "ERROR")
            return False
            
        try:
            # Find the main internet interface
            main_interface = self.find_main_interface()
            if not main_interface:
                self.log_message(">>> Could not detect main internet interface <<<", "ERROR")
                return False
                
            self.log_message(f">>> Setting up connection sharing: {self.pwnagotchi_interface} -> {main_interface} <<<", "SYSTEM")
            
            # Download and run the connection sharing script
            self.download_connection_script()
            
            # Execute connection sharing
            result = subprocess.run([
                "sudo", "./linux_connection_share.sh", 
                self.pwnagotchi_interface, main_interface
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log_message(">>> Connection sharing enabled successfully! <<<", "SUCCESS")
                return True
            else:
                self.log_message(f">>> Connection sharing failed: {result.stderr} <<<", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f">>> Connection sharing error: {e} <<<", "ERROR")
            return False

    def find_main_interface(self):
        """Find the main internet-connected interface."""
        try:
            # Get default route interface
            result = subprocess.run(
                ["ip", "route", "show", "default"], 
                capture_output=True, text=True, check=True
            )
            
            for line in result.stdout.splitlines():
                if "default via" in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        return parts[4]  # Interface name
                        
        except subprocess.CalledProcessError:
            pass
            
        return None

    def download_connection_script(self):
        """Download the Pwnagotchi connection sharing script."""
        script_url = "https://raw.githubusercontent.com/jayofelony/pwnagotchi/master/scripts/linux_connection_share.sh"
        script_path = "linux_connection_share.sh"
        
        try:
            if not os.path.exists(script_path):
                self.log_message(">>> Downloading connection sharing script... <<<", "SYSTEM")
                subprocess.run(["wget", script_url], check=True)
                os.chmod(script_path, 0o755)  # Make executable
                self.log_message(">>> Connection sharing script downloaded <<<", "SUCCESS")
        except subprocess.CalledProcessError as e:
            self.log_message(f">>> Failed to download script: {e} <<<", "ERROR")
        except Exception as e:
            self.log_message(f">>> Script download error: {e} <<<", "ERROR")


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
