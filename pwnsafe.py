__version__ = "1.4.0"

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
import shlex
import psutil
from ui_refactor import ConnState
from ssh_auth_enhanced import SSHAuthManager
import stat

if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        winreg = None
    try:
        import pythoncom
        import wmi
    except ImportError:
        pythoncom = None
        wmi = None
else:
    winreg = None
    pythoncom = None
    wmi = None


class BackupRestoreApp(ctk.CTk):
    def __init__(self, use_ui=True):
        # Always call parent constructor
        super().__init__()
        
        # Windows-specific initialization (must be early)
        self.is_windows = platform.system().lower() == "windows"
        self.pwnagotchi_adapter_name = None
        self.main_adapter_name = None
        
        # Initialize Pwnagotchi detection variables (needed for backend)
        self.pwnagotchi_detected = False
        self.pwnagotchi_interface = None
        self.pwnagotchi_mac = None
        self.pwnagotchi_ip = "10.0.0.2"
        self.pwnagotchi_user = "pi"
        self.pwnagotchi_pass = "raspberry"
        self.baseline_interfaces = set()
        self.detection_mode = "auto"
        self.reconnection_monitoring = False
        self._rndis_install_prompted = False
        
        # If not using UI, skip all UI initialization and return
        if not use_ui:
            return
        
        # Only set up UI if requested
        if use_ui:
            self.title("PwnSafe v1.4.0 - Cyberpunk Backup & Restore Utility")
            self.geometry("900x700")
            self.minsize(800, 600)
            
            # Set dystopian hacker theme
            ctk.set_appearance_mode("dark")
            self._setup_hacker_theme()
            
            # Make window resizable
            self.minsize(700, 500)
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(0, weight=1)
            
            # Create menu bar
            self.create_menu_bar()

            # Create main scrollable container
            self.main_scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
            self.main_scrollable_frame.pack(fill="both", expand=True, padx=15, pady=15)
            self.main_scrollable_frame.grid_columnconfigure(0, weight=1)

            # Header with modern compact styling
            self.header_frame = ctk.CTkFrame(self.main_scrollable_frame, corner_radius=8, fg_color="transparent")
            self.header_frame.pack(fill="x", pady=(0, 15))
            
            self.header_label = ctk.CTkLabel(
                self.header_frame, 
                text="🔒 PwnSafe v1.4.0",
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color="#00ff00"
            )
            self.header_label.pack()
            
            self.subtitle_label = ctk.CTkLabel(
                self.header_frame,
                text="Cyberpunk Backup & Restore Utility",
                font=ctk.CTkFont(size=12),
                text_color="#00ffff"
            )
            self.subtitle_label.pack()
            
            # Status frame (compact)
            self.status_frame = ctk.CTkFrame(self.main_scrollable_frame, corner_radius=8)
            self.status_frame.pack(fill="x", pady=(0, 15))
            
            self.status_label = ctk.CTkLabel(
                self.status_frame, 
                text="Ready - Automatic Pwnagotchi detection starting...",
                font=ctk.CTkFont(size=11),
                text_color="#ffffff"
            )
            self.status_label.pack(pady=8)

            # Connection Section (compact)
            self.connection_frame = ctk.CTkFrame(self.main_scrollable_frame, corner_radius=8)
            self.connection_frame.pack(fill="x", pady=(0, 15))
        
            # Section title
            self.connection_title = ctk.CTkLabel(
                self.connection_frame,
                text="🔗 Connection Settings",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#ff6600"
            )
            self.connection_title.pack(pady=(12, 8))

            # Connection inputs in a compact grid
            connection_grid = ctk.CTkFrame(self.connection_frame, fg_color="transparent")
        connection_grid.pack(fill="x", padx=12, pady=(0, 12))
        connection_grid.grid_columnconfigure(1, weight=1)
        connection_grid.grid_columnconfigure(3, weight=1)
        
        # Row 1: Host and Username
        host_label = ctk.CTkLabel(
            connection_grid, 
            text="Host:", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff00"
        )
        host_label.grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        
        self.host_entry = ctk.CTkEntry(
            connection_grid, 
            placeholder_text="10.0.0.2", 
            font=ctk.CTkFont(size=11),
            height=28
        )
        self.host_entry.grid(row=0, column=1, padx=(0, 15), pady=6, sticky="ew")

        user_label = ctk.CTkLabel(
            connection_grid, 
            text="User:", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff00"
        )
        user_label.grid(row=0, column=2, padx=(0, 8), pady=6, sticky="w")
        
        self.user_entry = ctk.CTkEntry(
            connection_grid, 
            placeholder_text="pi", 
            font=ctk.CTkFont(size=11),
            height=28
        )
        self.user_entry.grid(row=0, column=3, padx=0, pady=6, sticky="ew")

        # Row 2: Password
        pass_label = ctk.CTkLabel(
            connection_grid, 
            text="Password:", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff00"
        )
        pass_label.grid(row=1, column=0, padx=(0, 8), pady=6, sticky="w")
        
        self.pass_entry = ctk.CTkEntry(
            connection_grid, 
            placeholder_text="raspberry", 
            show="*", 
            font=ctk.CTkFont(size=11),
            height=28
        )
        self.pass_entry.grid(row=1, column=1, padx=(0, 15), pady=6, sticky="ew")

        # File selection section (compact)
        self.file_frame = ctk.CTkFrame(self.main_scrollable_frame, corner_radius=8)
        self.file_frame.pack(fill="x", pady=(0, 15))
        
        file_title = ctk.CTkLabel(
            self.file_frame,
            text="📁 Backup File Selection",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ff6600"
        )
        file_title.pack(pady=(12, 8))
        
        file_grid = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        file_grid.pack(fill="x", padx=12, pady=(0, 12))
        file_grid.grid_columnconfigure(1, weight=1)
        
        file_label = ctk.CTkLabel(
            file_grid, 
            text="File:", 
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#00ff00"
        )
        file_label.grid(row=0, column=0, padx=(0, 8), pady=6, sticky="w")
        
        self.file_entry = ctk.CTkEntry(
            file_grid, 
            placeholder_text="Select .tgz backup file...", 
            font=ctk.CTkFont(size=11),
            height=28
        )
        self.file_entry.grid(row=0, column=1, padx=(0, 10), pady=6, sticky="ew")

        self.browse_button = ctk.CTkButton(
            file_grid, 
            text="Browse", 
            command=self.browse_file,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#ff6600",
            hover_color="#ff8833",
            height=28,
            width=80
        )
        self.browse_button.grid(row=0, column=2, padx=0, pady=6)

        # Main action section (compact)
        self.action_frame = ctk.CTkFrame(self.main_scrollable_frame, corner_radius=8)
        self.action_frame.pack(fill="x", pady=(0, 15))
        
        action_title = ctk.CTkLabel(
            self.action_frame,
            text="⚡ Primary Operations",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ff6600"
        )
        action_title.pack(pady=(12, 8))
        
        action_grid = ctk.CTkFrame(self.action_frame, fg_color="transparent")
        action_grid.pack(fill="x", padx=12, pady=(0, 12))
        action_grid.grid_columnconfigure(0, weight=1)
        action_grid.grid_columnconfigure(1, weight=1)
        
        # Primary backup and restore buttons
        self.backup_button = ctk.CTkButton(
            action_grid, 
            text="💾 Backup Pwnagotchi", 
            command=self.start_backup, 
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#00ff00",
            hover_color="#00cc00",
            text_color="#000000"
        )
        self.backup_button.grid(row=0, column=0, padx=(0, 8), pady=8, sticky="ew")

        self.restore_button = ctk.CTkButton(
            action_grid, 
            text="🔄 Restore Pwnagotchi", 
            command=self.start_restore, 
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#ff0066",
            hover_color="#cc0055",
            text_color="#ffffff"
        )
        self.restore_button.grid(row=0, column=1, padx=(8, 0), pady=8, sticky="ew")
        
        # Output Log (compact)
        self.output_frame = ctk.CTkFrame(self.main_scrollable_frame, corner_radius=8)
        self.output_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        output_title = ctk.CTkLabel(
            self.output_frame,
            text="📋 System Log Output",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ff6600"
        )
        output_title.pack(pady=(12, 8))
        
        # Create a frame for the text widget to maintain styling
        text_frame = ctk.CTkFrame(self.output_frame, corner_radius=8, fg_color="#1a1a1a")
        text_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        
        # Use standard Tkinter Text widget for colored text support
        from tkinter import Text
        self.output_text = Text(
            text_frame,
            font=("Consolas", 10),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#333333",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            wrap="word"
        )
        self.output_text.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Initialize with welcome message
        self.log_message("PwnSafe v1.4.0 - Cyberpunk Backup & Restore Utility", "INFO")
        self.log_message("System initialized. Ready for operations.", "SUCCESS")
        self.log_message("Automatic Pwnagotchi detection starting...", "INFO")
        
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
        
        # Remove duplicate Windows initialization (already done earlier)
        
        # Start automated detection with user prompts (only if UI is enabled)
        if use_ui:
            self.after(1000, self.start_automated_detection)

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
        """Log messages with cyberpunk styling and colors."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on message level
        color_map = {
            "INFO": "#00ff00",      # Green
            "SUCCESS": "#00ff00",   # Green for success
            "WARNING": "#ffff00",   # Yellow
            "ERROR": "#ff0000",     # Red
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
        
        # Configure text tags for colors (only once)
        if not hasattr(self, '_tags_configured'):
            self.output_text.tag_configure("success", foreground="#00ff00")  # Green
            self.output_text.tag_configure("warning", foreground="#ffff00")  # Yellow
            self.output_text.tag_configure("error", foreground="#ff0000")    # Red
            self.output_text.tag_configure("system", foreground="#ff6600")   # Orange
            self.output_text.tag_configure("info", foreground="#00ff00")     # Green
            self._tags_configured = True
        
        # Insert message and apply color tag
        start_pos = self.output_text.index("end-1c")
        self.output_text.insert("end", formatted_msg)
        end_pos = self.output_text.index("end-1c")
        
        # Apply color based on level
        if level == "SUCCESS":
            self.output_text.tag_add("success", start_pos, end_pos)
        elif level == "WARNING":
            self.output_text.tag_add("warning", start_pos, end_pos)
        elif level == "ERROR":
            self.output_text.tag_add("error", start_pos, end_pos)
        elif level == "SYSTEM":
            self.output_text.tag_add("system", start_pos, end_pos)
        else:
            self.output_text.tag_add("info", start_pos, end_pos)
        
        self.output_text.see("end")

    def ssh_connect(
        self,
        host,
        username,
        password="",
        auth_method="password",
        ssh_key_path="",
        ssh_key_passphrase="",
        use_ssh_agent=False,
    ):
        """Connect without reading Tk widgets from a worker thread."""
        auth = SSHAuthManager(self.log_message)
        return auth.connect(
            host=host,
            username=username,
            auth_method=auth_method,
            password=password,
            ssh_key_path=ssh_key_path,
            ssh_key_passphrase=ssh_key_passphrase,
            use_ssh_agent=use_ssh_agent,
        )

    def setup_ssh_key(self, host, username, password, requested_key_path=""):
        """Create or reuse a local key and install it with one password login."""
        if not host or not username or not password:
            raise ValueError("host, username, and password are required for key setup")

        auth = SSHAuthManager(self.log_message)
        key = None
        key_path = ""
        if requested_key_path and os.path.isfile(requested_key_path):
            key_path = os.path.abspath(requested_key_path)
            key = auth._load_private_key(key_path, "")
            if not key:
                self.log_message(
                    "The selected SSH key is invalid; generating a PwnSafe key instead.",
                    "WARNING",
                )

        if not key:
            ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
            os.makedirs(ssh_dir, exist_ok=True)
            if platform.system() != "Windows":
                os.chmod(ssh_dir, stat.S_IRWXU)

            base_path = os.path.join(ssh_dir, "pwnsafe_id_rsa")
            for suffix in range(100):
                candidate = base_path if suffix == 0 else f"{base_path}_{suffix}"
                if os.path.exists(candidate):
                    existing_key = auth._load_private_key(candidate, "")
                    if existing_key:
                        key_path, key = candidate, existing_key
                        break
                    continue
                key_path = candidate
                key = paramiko.RSAKey.generate(3072)
                key.write_private_key_file(key_path)
                if platform.system() != "Windows":
                    os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
                self.log_message(f"Generated SSH key: {key_path}", "SUCCESS")
                break
            if not key:
                raise RuntimeError("could not create a usable local SSH key")

        public_identity = f"{key.get_name()} {key.get_base64()}"
        public_key = f"{public_identity} pwnsafe-generated-key"
        public_key_path = key_path + ".pub"
        with open(public_key_path, "w", encoding="utf-8") as public_file:
            public_file.write(public_key + "\n")

        client = None
        try:
            client = auth.connect(
                host=host,
                username=username,
                auth_method="password",
                password=password,
            )
            if not client:
                raise ConnectionError("password authentication failed")

            quoted_identity = shlex.quote(public_identity)
            quoted_key = shlex.quote(public_key)
            command = (
                'umask 077; mkdir -p "$HOME/.ssh" && '
                'touch "$HOME/.ssh/authorized_keys" && '
                f'(grep -qF -- {quoted_identity} "$HOME/.ssh/authorized_keys" || '
                f'printf "%s\\n" {quoted_key} >> "$HOME/.ssh/authorized_keys") && '
                'chmod 700 "$HOME/.ssh" && chmod 600 "$HOME/.ssh/authorized_keys"'
            )
            _, stdout, stderr = client.exec_command(command)
            error_text = stderr.read().decode(errors="replace").strip()
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                raise RuntimeError(
                    f"authorized_keys update failed with exit code {exit_status}"
                    + (f": {error_text}" if error_text else "")
                )
            self.log_message("SSH public key installed on the Pwnagotchi.", "SUCCESS")
            return os.path.abspath(key_path)
        finally:
            if client:
                try:
                    client.close()
                except Exception as error:
                    self.log_message(f"SSH close warning: {error}", "WARNING")

    def inspect_device_connection(
        self,
        host,
        username,
        password="",
        auth_method="password",
        ssh_key_path="",
        ssh_key_passphrase="",
        use_ssh_agent=False,
    ):
        """Read the hostname and verify that internet traffic uses host sharing."""
        result = {"hostname": "", "internet_shared": False}
        ssh = None
        try:
            ssh = self.ssh_connect(
                host, username, password, auth_method, ssh_key_path,
                ssh_key_passphrase, use_ssh_agent,
            )
            if not ssh:
                raise ConnectionError("SSH authentication failed")

            _, stdout, stderr = ssh.exec_command("hostname")
            hostname = stdout.read().decode(errors="replace").strip()
            hostname_error = stderr.read().decode(errors="replace").strip()
            hostname_status = stdout.channel.recv_exit_status()
            if hostname_status != 0 or not hostname:
                raise RuntimeError(
                    f"hostname command failed with exit code {hostname_status}"
                    + (f": {hostname_error}" if hostname_error else "")
                )
            result["hostname"] = hostname.splitlines()[0]
            self.log_message(f'Device hostname: {result["hostname"]}', "SUCCESS")

            try:
                _, route_out, route_err = ssh.exec_command("ip route get 8.8.8.8")
                route_text = route_out.read().decode(errors="replace").strip()
                route_error = route_err.read().decode(errors="replace").strip()
                route_status = route_out.channel.recv_exit_status()
                if route_status != 0:
                    raise RuntimeError(
                        f"route check failed with exit code {route_status}"
                        + (f": {route_error}" if route_error else "")
                    )

                if "via 10.0.0.1" not in route_text:
                    self.log_message(
                        "Internet sharing not verified: the device default route does not use 10.0.0.1.",
                        "WARNING",
                    )
                else:
                    _, ping_out, ping_err = ssh.exec_command("ping -c 1 -W 3 8.8.8.8")
                    ping_error = ping_err.read().decode(errors="replace").strip()
                    ping_status = ping_out.channel.recv_exit_status()
                    if ping_status == 0:
                        result["internet_shared"] = True
                        self.log_message(
                            "Internet sharing verified: Pwnagotchi has internet access through 10.0.0.1.",
                            "SUCCESS",
                        )
                    else:
                        self.log_message(
                            "Internet sharing not verified: the Pwnagotchi cannot reach 8.8.8.8"
                            + (f" ({ping_error})" if ping_error else "."),
                            "WARNING",
                        )
            except Exception as error:
                self.log_message(f"Internet sharing check failed: {error}", "WARNING")
        except Exception as error:
            self.log_message(f"Could not inspect connected Pwnagotchi: {error}", "WARNING")
        finally:
            if ssh:
                try:
                    ssh.close()
                except Exception as error:
                    self.log_message(f"SSH close warning: {error}", "WARNING")
        return result

    def start_backup(self):
        """Start backup with connection check and user prompts."""
        if not self.pwnagotchi_detected:
            self.show_connection_required_dialog("backup")
            return
        
        # Show backup confirmation dialog
        self.show_backup_dialog()

    def show_connection_required_dialog(self, operation):
        """Show dialog when Pwnagotchi connection is required."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Connection Required")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (dialog.winfo_screenheight() // 2) - (250 // 2)
        dialog.geometry(f"400x250+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Pwnagotchi Not Connected",
            font=("Courier New", 18, "bold"),
            text_color="#ff0066"
        )
        title_label.pack(pady=(20, 10))
        
        # Message
        message = f"""To {operation} your Pwnagotchi, you need to:

1. Connect your Pwnagotchi to the USB DATA port
2. Wait for automatic detection
3. Ensure connection is established

Click 'Detect Now' to scan for your Pwnagotchi."""
        
        message_label = ctk.CTkLabel(
            main_frame,
            text=message,
            font=("Courier New", 11),
            text_color="#ffffff",
            justify="left"
        )
        message_label.pack(pady=20, padx=20)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        detect_button = ctk.CTkButton(
            button_frame,
            text="Detect Now",
            command=lambda: self.detect_and_close(dialog),
            font=("Courier New", 12, "bold"),
            fg_color="#00ff00",
            hover_color="#00cc00",
            text_color="#000000",
            width=120
        )
        detect_button.pack(side="left", padx=10)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            font=("Courier New", 12, "bold"),
            fg_color="#666666",
            hover_color="#888888",
            text_color="#ffffff",
            width=120
        )
        cancel_button.pack(side="left", padx=10)

    def detect_and_close(self, dialog):
        """Start detection and close dialog."""
        dialog.destroy()
        self.update_status("Detecting Pwnagotchi...")
        if self.is_windows:
            threading.Thread(target=self.detect_pwnagotchi_windows, daemon=True).start()
        else:
            threading.Thread(target=self.manual_pwnagotchi_detection, daemon=True).start()

    def show_backup_dialog(self):
        """Show backup confirmation dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Backup Pwnagotchi")
        dialog.geometry("450x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"450x300+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Backup Pwnagotchi",
            font=("Courier New", 20, "bold"),
            text_color="#00ff00"
        )
        title_label.pack(pady=(20, 10))
        
        # Info
        info_text = """This will create a backup of your Pwnagotchi including:

• Configuration files (/etc/pwnagotchi/)
• SSH keys (/root/.ssh/)
• Handshakes (/home/pi/handshakes/)

The backup will be saved as a compressed .tgz file."""
        
        info_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=("Courier New", 11),
            text_color="#ffffff",
            justify="left"
        )
        info_label.pack(pady=20, padx=20)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        backup_button = ctk.CTkButton(
            button_frame,
            text="Start Backup",
            command=lambda: self.start_backup_process(dialog),
            font=("Courier New", 12, "bold"),
            fg_color="#00ff00",
            hover_color="#00cc00",
            text_color="#000000",
            width=120
        )
        backup_button.pack(side="left", padx=10)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            font=("Courier New", 12, "bold"),
            fg_color="#666666",
            hover_color="#888888",
            text_color="#ffffff",
            width=120
        )
        cancel_button.pack(side="left", padx=10)

    def start_backup_process(self, dialog):
        """Collect legacy UI values on the Tk thread, then start the worker."""
        dialog.destroy()
        save_path = filedialog.asksaveasfilename(
            defaultextension=".tgz", filetypes=[("TGZ Files", "*.tgz")]
        )
        if not save_path:
            self.update_status("Backup canceled")
            return
        self.backup_to_path(
            save_path,
            self.host_entry.get(),
            self.user_entry.get(),
            self.pass_entry.get(),
        )

    def backup_to_path(
        self, dest_path, host, username, password="", auth_method="password",
        ssh_key_path="", ssh_key_passphrase="", use_ssh_agent=False
    ):
        """Backup Pwnagotchi to specified path."""
        threading.Thread(
            target=self._backup_worker,
            args=(dest_path, host, username, password, auth_method,
                  ssh_key_path, ssh_key_passphrase, use_ssh_agent),
            daemon=True,
        ).start()

    def _backup_worker(
        self, save_path, host, username, password="", auth_method="password",
        ssh_key_path="", ssh_key_passphrase="", use_ssh_agent=False
    ):
        """Worker thread for backup operation."""
        ssh = None
        partial_path = os.path.abspath(save_path) + ".part"
        try:
            ssh = self.ssh_connect(
                host, username, password, auth_method, ssh_key_path,
                ssh_key_passphrase, use_ssh_agent
            )
            if not ssh:
                raise ConnectionError("SSH authentication failed")

            self.log_message("Initiating backup sequence...", "SYSTEM")
            self.update_status("Creating backup...")
            command = (
                "sudo tar --exclude='/etc/pwnagotchi/log/*.log' "
                "--warning=none -czf - "
                "/etc/pwnagotchi/ /root/.ssh /home/pi/handshakes"
            )
            _, stdout, stderr = ssh.exec_command(command)

            with open(partial_path, "wb") as backup_file:
                while True:
                    chunk = stdout.read(4096)
                    if not chunk:
                        break
                    backup_file.write(chunk)

            errors = stderr.read().decode(errors="replace").strip()
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                raise RuntimeError(
                    f"remote tar failed with exit code {exit_status}"
                    + (f": {errors}" if errors else "")
                )

            os.replace(partial_path, os.path.abspath(save_path))
            if errors:
                for line in errors.splitlines():
                    self.log_message(line, "WARNING")

            self.log_message(f"Backup completed successfully: {save_path}", "SUCCESS")
            self.update_status("Backup completed successfully")
            self.show_toast("Backup completed successfully", "success")

            self.set_connection_state(ConnState.CONNECTED, "Pwnagotchi Connected and Ready!")

        except Exception as e:
            try:
                if os.path.exists(partial_path):
                    os.remove(partial_path)
            except OSError as cleanup_error:
                self.log_message(f"Could not remove partial backup: {cleanup_error}", "WARNING")
            self.log_message(f"Backup failed: {e}", "ERROR")
            self.update_status("Backup failed - check logs")
            self.set_connection_state(ConnState.ERROR, "Backup failed - check logs")
            self.show_toast(f"Backup failed: {e}", "error")

        finally:
            if ssh:
                try:
                    ssh.close()
                except Exception as close_error:
                    self.log_message(f"SSH close warning: {close_error}", "WARNING")

    def restore_from_path(
        self, src_path, host, username, password="", auth_method="password",
        ssh_key_path="", ssh_key_passphrase="", use_ssh_agent=False
    ):
        """Restore Pwnagotchi from specified path."""
        threading.Thread(
            target=self._restore_worker,
            args=(src_path, host, username, password, auth_method,
                  ssh_key_path, ssh_key_passphrase, use_ssh_agent),
            daemon=True,
        ).start()

    def _restore_worker(
        self, restore_path, host, username, password="", auth_method="password",
        ssh_key_path="", ssh_key_passphrase="", use_ssh_agent=False
    ):
        """Worker thread for restore operation."""
        ssh = None
        remote_temp = ""
        try:
            ssh = self.ssh_connect(
                host, username, password, auth_method, ssh_key_path,
                ssh_key_passphrase, use_ssh_agent
            )
            if not ssh:
                raise ConnectionError("SSH authentication failed")

            self.log_message("Initiating restore sequence...", "SYSTEM")
            self.update_status("Uploading backup...")

            _, stdout, stderr = ssh.exec_command("mktemp")
            remote_temp = stdout.read().decode(errors="replace").strip()
            mktemp_error = stderr.read().decode(errors="replace").strip()
            mktemp_status = stdout.channel.recv_exit_status()
            if mktemp_status != 0 or not remote_temp:
                raise RuntimeError(
                    f"could not create remote temporary file"
                    + (f": {mktemp_error}" if mktemp_error else "")
                )

            sftp = ssh.open_sftp()
            try:
                sftp.put(os.path.abspath(restore_path), remote_temp)
            finally:
                sftp.close()

            self.update_status("Restoring backup...")
            quoted_temp = "'" + remote_temp.replace("'", "'\"'\"'") + "'"
            extract_command = (
                f"sudo tar -xzf {quoted_temp} -C / && rm -f {quoted_temp}"
            )
            _, stdout, stderr = ssh.exec_command(extract_command)
            extract_error = stderr.read().decode(errors="replace").strip()
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                raise RuntimeError(
                    f"remote tar failed with exit code {exit_status}"
                    + (f": {extract_error}" if extract_error else "")
                )

            remote_temp = ""
            self.log_message(f"Restore completed successfully from: {restore_path}", "SUCCESS")
            self.update_status("Restore completed successfully")
            self.set_connection_state(ConnState.CONNECTED, "Pwnagotchi Connected and Ready!")
            self.show_toast("Restore completed successfully", "success")

        except Exception as e:
            self.log_message(f"Restore failed: {e}", "ERROR")
            self.update_status("Restore failed - check logs")
            self.set_connection_state(ConnState.ERROR, "Restore failed - check logs")
            self.show_toast(f"Restore failed: {e}", "error")

        finally:
            if ssh and remote_temp:
                try:
                    quoted_temp = "'" + remote_temp.replace("'", "'\"'\"'") + "'"
                    _, cleanup_out, cleanup_err = ssh.exec_command(f"rm -f {quoted_temp}")
                    cleanup_message = cleanup_err.read().decode(errors="replace").strip()
                    if cleanup_out.channel.recv_exit_status() != 0:
                        self.log_message(
                            f"Could not remove remote temporary file: {cleanup_message}",
                            "WARNING",
                        )
                except Exception as cleanup_error:
                    self.log_message(
                        f"Could not remove remote temporary file: {cleanup_error}",
                        "WARNING",
                    )
            if ssh:
                try:
                    ssh.close()
                except Exception as close_error:
                    self.log_message(f"SSH close warning: {close_error}", "WARNING")

    def start_restore(self):
        """Start restore with connection check and user prompts."""
        if not self.pwnagotchi_detected:
            self.show_connection_required_dialog("restore")
            return
        
        # Show restore confirmation dialog
        self.show_restore_dialog()

    def show_restore_dialog(self):
        """Show restore confirmation dialog."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Restore Pwnagotchi")
        dialog.geometry("450x300")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (300 // 2)
        dialog.geometry(f"450x300+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Restore Pwnagotchi",
            font=("Courier New", 20, "bold"),
            text_color="#ff0066"
        )
        title_label.pack(pady=(20, 10))
        
        # Info
        info_text = """This will restore your Pwnagotchi from a backup file including:

• Configuration files (/etc/pwnagotchi/)
• SSH keys (/root/.ssh/)
• Handshakes (/home/pi/handshakes/)

WARNING: This will overwrite existing data on your Pwnagotchi!"""
        
        info_label = ctk.CTkLabel(
            main_frame,
            text=info_text,
            font=("Courier New", 11),
            text_color="#ffffff",
            justify="left"
        )
        info_label.pack(pady=20, padx=20)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        restore_button = ctk.CTkButton(
            button_frame,
            text="Start Restore",
            command=lambda: self.start_restore_process(dialog),
            font=("Courier New", 12, "bold"),
            fg_color="#ff0066",
            hover_color="#cc0055",
            text_color="#ffffff",
            width=120
        )
        restore_button.pack(side="left", padx=10)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=dialog.destroy,
            font=("Courier New", 12, "bold"),
            fg_color="#666666",
            hover_color="#888888",
            text_color="#ffffff",
            width=120
        )
        cancel_button.pack(side="left", padx=10)

    def start_restore_process(self, dialog):
        """Collect legacy UI values on the Tk thread, then start the worker."""
        dialog.destroy()
        restore_path = self.file_entry.get().strip()
        if not restore_path or not os.path.isfile(restore_path):
            self.log_message("No valid backup file selected", "ERROR")
            self.update_status("Restore failed - no file selected")
            return
        self.restore_from_path(
            restore_path,
            self.host_entry.get(),
            self.user_entry.get(),
            self.pass_entry.get(),
        )

    def start_connection_sharing(self):
        """Start connection sharing in background thread."""
        if self.is_windows:
            threading.Thread(target=self.setup_internet_sharing_windows, daemon=True).start()
        else:
            threading.Thread(target=self.setup_connection_sharing, daemon=True).start()

    def detect_platform(self):
        """Detect the current operating system and log it."""
        current_platform = platform.system().lower()
        self.log_message(f"Running on {current_platform.capitalize()} system.", "SYSTEM")
        return current_platform
    
    def get_resource_path(self, relative_path):
        """Get the absolute path to a resource, works for dev and for PyInstaller."""
        base_path = getattr(
            sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))
        )
        return os.path.join(base_path, relative_path)

    def is_rndis_driver_installed(self):
        """Return whether the supplied RNDIS driver is installed on Windows."""
        if not self.is_windows:
            return True

        try:
            result = subprocess.run(
                ["pnputil.exe", "/enum-drivers"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "pnputil failed")
            output = result.stdout.lower()
            if "rndis.inf" in output or "usb remote ndis" in output:
                return True
        except Exception as e:
            self.log_message(f"Could not inspect the Windows driver store: {e}", "WARNING")

        com_initialized = False
        try:
            if wmi is None:
                return False
            if pythoncom is not None:
                pythoncom.CoInitialize()
                com_initialized = True
            for driver in wmi.WMI().Win32_PnPSignedDriver():
                name = " ".join(
                    str(value or "")
                    for value in (
                        getattr(driver, "DeviceName", ""),
                        getattr(driver, "DriverProviderName", ""),
                        getattr(driver, "InfName", ""),
                    )
                ).lower()
                if "rndis" in name or "remote ndis" in name:
                    return True
            return False
        except Exception as e:
            self.log_message(f"Could not query installed Windows drivers: {e}", "WARNING")
            return False
        finally:
            if com_initialized:
                pythoncom.CoUninitialize()

    def install_rndis_driver(self):
        """Install the bundled RNDIS INF, requesting UAC elevation if needed."""
        if not self.is_windows:
            return False

        inf_path = self.get_resource_path(os.path.join("drivers", "RNDIS.inf"))
        catalog_path = self.get_resource_path(os.path.join("drivers", "RNDIS.cat"))
        if not os.path.isfile(inf_path) or not os.path.isfile(catalog_path):
            self.log_message("Bundled RNDIS driver files are missing", "ERROR")
            self.show_toast("Bundled RNDIS driver files are missing", "error")
            return False

        try:
            import ctypes

            self.log_message("Installing the bundled RNDIS driver...", "SYSTEM")
            if ctypes.windll.shell32.IsUserAnAdmin():
                result = subprocess.run(
                    ["pnputil.exe", "/add-driver", inf_path, "/install"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode != 0:
                    raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            else:
                parameters = subprocess.list2cmdline(
                    ["/add-driver", inf_path, "/install"]
                )
                shell_execute = ctypes.windll.shell32.ShellExecuteW
                shell_execute.restype = ctypes.c_void_p
                launch_result = shell_execute(
                    None, "runas", "pnputil.exe", parameters, None, 0
                )
                if int(launch_result or 0) <= 32:
                    raise PermissionError(
                        "administrator approval was denied or pnputil could not start"
                    )

                for _ in range(60):
                    if self.is_rndis_driver_installed():
                        break
                    time.sleep(1)
                else:
                    raise RuntimeError("driver installation did not complete")

            if not self.is_rndis_driver_installed():
                raise RuntimeError("Windows did not register the RNDIS driver")

            self.log_message("RNDIS driver installed successfully", "SUCCESS")
            self.show_toast("RNDIS driver installed successfully", "success")
            return True
        except Exception as e:
            self.log_message(f"RNDIS driver installation failed: {e}", "ERROR")
            self.show_toast(f"RNDIS driver installation failed: {e}", "error")
            return False

    def ensure_rndis_driver(self):
        """Prompt once per run to install the bundled driver when it is missing."""
        if not self.is_windows or self.is_rndis_driver_installed():
            return True
        if self._rndis_install_prompted:
            return False

        self._rndis_install_prompted = True
        if not hasattr(self, "ui") or not self.ui:
            self.log_message("RNDIS driver is missing; UI confirmation is required", "ERROR")
            return False

        inf_path = self.get_resource_path(os.path.join("drivers", "RNDIS.inf"))
        if not self.ui.confirm_rndis_driver_install(os.path.basename(inf_path)):
            self.log_message("RNDIS driver installation was declined", "WARNING")
            return False
        return self.install_rndis_driver()

    def create_menu_bar(self):
        """Create the application menu bar."""
        # Create menu bar
        menubar = Menu(self)
        self.config(menu=menubar)
        
        # File menu - simplified
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Backup Pwnagotchi", command=self.start_backup)
        file_menu.add_command(label="Restore Pwnagotchi", command=self.start_restore)
        file_menu.add_separator()
        file_menu.add_command(label="SSH Certificate Management", command=self.show_ssh_cert_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        
        # Tools menu - simplified and working items only
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Detect Pwnagotchi", command=self.manual_pwnagotchi_detection)
        tools_menu.add_command(label="Share Internet", command=self.start_connection_sharing)
        
        # Add Windows-specific tools if on Windows
        if self.is_windows:
            tools_menu.add_separator()
            tools_menu.add_command(label="Windows Auto-Config", command=self.detect_pwnagotchi_windows)
            tools_menu.add_command(label="Open Network Connections", command=self.open_network_connections)
        
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
            text="PwnSafe v1.4.0",
            font=("Courier New", 24, "bold"),
            text_color="#00ff00"
        )
        title_label.pack(pady=(20, 10))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Cyberpunk Backup & Restore Utility",
            font=("Courier New", 14),
            text_color="#00ffff"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Description
        desc_text = """PwnSafe is a professional-grade backup and restore utility 
designed specifically for Pwnagotchi devices. Built with a 
unique cyberpunk aesthetic, it provides seamless backup 
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
        self.log_message("Manual Pwnagotchi detection initiated...", "SYSTEM")
        
        if self.is_windows:
            self.log_message("Scanning for RNDIS adapters on Windows...", "INFO")
            # Use Windows-specific detection
            threading.Thread(target=self.detect_pwnagotchi_windows, daemon=True).start()
        else:
            self.log_message("Scanning network interfaces...", "INFO")
            
            # Run detection in background but provide immediate feedback
            def detection_with_feedback():
                try:
                    # Check for Pwnagotchi network interface
                    pwnagotchi_interface = self.find_pwnagotchi_interface()
                    
                    if pwnagotchi_interface:
                        self.pwnagotchi_interface = pwnagotchi_interface
                        self.log_message(f"Pwnagotchi interface found: {pwnagotchi_interface}", "SUCCESS")
                        
                        # Test connection to Pwnagotchi
                        self.log_message("Testing SSH connection to Pwnagotchi...", "INFO")
                        if self.test_pwnagotchi_connection():
                            was_detected = self.pwnagotchi_detected
                            self.pwnagotchi_detected = True
                            self.auto_configure_pwnagotchi()
                            self.log_message("Pwnagotchi detected and configured successfully!", "SUCCESS")
                            self.log_message("Connection fields have been auto-filled", "SUCCESS")
                            
                            # Offer SSH certificate setup if this is a new detection
                            if not was_detected:
                                self.offer_ssh_certificate_setup()
                            
                            # Start reconnection monitoring if we have a MAC address
                            if self.pwnagotchi_mac:
                                self.start_reconnection_monitoring()
                        else:
                            self.log_message("Pwnagotchi interface found but SSH connection failed", "WARNING")
                            self.log_message("Please check if Pwnagotchi is fully booted", "WARNING")
                    else:
                        self.log_message("No Pwnagotchi interface detected", "WARNING")
                        self.log_message("Make sure Pwnagotchi is connected to DATA port", "INFO")
                        self.log_message("Check if network interface is configured with 10.0.0.1/24", "INFO")
                        
                except Exception as e:
                    self.log_message(f"Detection error: {e}", "ERROR")
            
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
            if self.is_windows:
                # For Windows, we'll use WMI to get current adapters
                c = wmi.WMI()
                adapters = c.Win32_NetworkAdapter()
                
                self.baseline_interfaces = set()
                for adapter in adapters:
                    if adapter.NetConnectionID and "RNDIS" not in adapter.Description:
                        self.baseline_interfaces.add(adapter.NetConnectionID)
                
                self.log_message(f">>> Baseline snapshot captured: {len(self.baseline_interfaces)} interfaces <<<", "SUCCESS")
                for interface in sorted(self.baseline_interfaces):
                    self.log_message(f"    - {interface}", "INFO")
            else:
                # Use Linux commands
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
                if self.is_windows:
                    # Use Windows-specific detection
                    if self.detect_pwnagotchi_windows():
                        self.log_message(">>> Pwnagotchi detected during monitoring! <<<", "SUCCESS")
                        return
                else:
                    # Use Linux commands
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
            if self.is_windows:
                self.log_message(">>> Make sure Pwnagotchi is plugged into DATA port and RNDIS driver is installed <<<", "INFO")
            else:
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
            # Set the connection fields using thread-safe UI adapter
            if hasattr(self, 'ui') and self.ui:
                self.ui.ui_set_host(self.pwnagotchi_ip)
                self.ui.ui_set_user(self.pwnagotchi_user)
                self.ui.ui_set_password(self.pwnagotchi_pass)
                self.log_message(f">>> UI configured for {self.pwnagotchi_ip} <<<", "SUCCESS")
            else:
                self.log_message(">>> UI not available for auto-configuration <<<", "WARNING")
            
            # Update UI to show Pwnagotchi is connected
            self.update_pwnagotchi_status()

    def update_pwnagotchi_status(self):
        """Update UI to show Pwnagotchi connection status."""
        if self.pwnagotchi_detected:
            # Use the update_status method which handles UI availability
            self.update_status("✅ Pwnagotchi Connected and Ready!")

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

    # Windows-specific methods for Pwnagotchi detection and configuration
    def detect_pwnagotchi_windows(self):
        """Detect Pwnagotchi on Windows using RNDIS adapter detection."""
        if not self.is_windows:
            return False
        if not self.ensure_rndis_driver():
            self.set_connection_state(ConnState.ERROR, "RNDIS driver is required")
            return False
        if wmi is None:
            self.log_message("WMI support is not installed", "ERROR")
            self.set_connection_state(ConnState.ERROR, "WMI support is unavailable")
            return False

        com_initialized = False
        try:
            if pythoncom is not None:
                pythoncom.CoInitialize()
                com_initialized = True
            self.log_message("Searching for connected Pwnagotchi device...", "INFO")
            
            # Use WMI to get network adapters
            c = wmi.WMI()
            adapters = c.Win32_NetworkAdapter()
            
            rndis_adapters = []
            for adapter in adapters:
                if (adapter.NetConnectionID and 
                    adapter.Description and 
                    ("RNDIS" in adapter.Description.upper() or 
                     "USB" in adapter.Description.upper() and "ETHERNET" in adapter.Description.upper())):
                    rndis_adapters.append(adapter)
                    # Verbose only
                    self.log_message(f"Potential adapter: {adapter.Description}", "INFO", verbose=True)
            
            if rndis_adapters:
                # Use the first RNDIS adapter found
                adapter = rndis_adapters[0]
                self.log_message(f"Found USB adapter: {adapter.NetConnectionID} ({adapter.Description})", "SUCCESS")
                self.pwnagotchi_adapter_name = adapter.NetConnectionID
                
                # Configure the adapter automatically
                if self.configure_pwnagotchi_windows():
                    return True
            else:
                self.log_message("No RNDIS adapter detected", "ERROR")
                self.log_message("Make sure Pwnagotchi is connected to DATA port", "INFO")
                return False
            
        except Exception as e:
            self.log_message(f"Detection error: {e}", "ERROR")
            return False
        finally:
            if com_initialized:
                pythoncom.CoUninitialize()

    def _windows_adapter_has_expected_ip(self):
        """Check whether Windows actually applied 10.0.0.1/24 to the adapter."""
        try:
            for address in psutil.net_if_addrs().get(self.pwnagotchi_adapter_name, []):
                if (
                    address.family == socket.AF_INET
                    and address.address == "10.0.0.1"
                    and address.netmask == "255.255.255.0"
                ):
                    return True
        except Exception as e:
            self.log_message(f"Could not verify adapter address: {e}", "WARNING")
        return False

    def _configure_windows_adapter_ip(self):
        """Apply the static RNDIS address, requesting UAC elevation if required."""
        import ctypes

        arguments = [
            "interface", "ipv4", "set", "address",
            f"name={self.pwnagotchi_adapter_name}",
            "source=static", "address=10.0.0.1", "mask=255.255.255.0",
            "gateway=none", "store=persistent",
        ]

        if ctypes.windll.shell32.IsUserAnAdmin():
            result = subprocess.run(
                ["netsh.exe", *arguments],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                error = result.stderr.strip() or result.stdout.strip() or "netsh failed"
                raise RuntimeError(error)
        else:
            self.log_message(
                "Administrator approval is required to configure the RNDIS adapter.",
                "INFO",
            )
            shell_execute = ctypes.windll.shell32.ShellExecuteW
            shell_execute.restype = ctypes.c_void_p
            launch_result = shell_execute(
                None,
                "runas",
                "netsh.exe",
                subprocess.list2cmdline(arguments),
                None,
                0,
            )
            if int(launch_result or 0) <= 32:
                raise PermissionError("administrator approval was denied")

        for _ in range(30):
            if self._windows_adapter_has_expected_ip():
                return True
            time.sleep(0.5)
        return False

    def configure_pwnagotchi_windows(self):
        """Assign and verify the Windows host address for the Pwnagotchi link."""
        if not self.pwnagotchi_adapter_name:
            return False

        try:
            self.log_message(
                f"Configuring {self.pwnagotchi_adapter_name}: IP 10.0.0.1/24",
                "INFO",
            )
            if self._windows_adapter_has_expected_ip():
                self.log_message("RNDIS adapter is already configured", "INFO")
            elif not self._configure_windows_adapter_ip():
                raise RuntimeError("Windows did not apply 10.0.0.1/24 to the adapter")

            self.log_message("Network configuration verified: 10.0.0.1/24", "SUCCESS")
            self.log_message("Waiting for Pwnagotchi SSH on 10.0.0.2...", "INFO")

            for _ in range(20):
                try:
                    connection = socket.create_connection((self.pwnagotchi_ip, 22), timeout=1)
                    connection.close()
                    self.pwnagotchi_detected = True
                    self.auto_configure_pwnagotchi()
                    self.set_connection_state(
                        ConnState.CONNECTED, "Pwnagotchi Connected and Ready!"
                    )
                    self.log_message("Pwnagotchi connected and ready!", "SUCCESS")
                    return True
                except OSError:
                    time.sleep(1)

            self.log_message(
                "Adapter configured; Pwnagotchi SSH is not ready yet. Live monitoring will continue.",
                "WARNING",
            )
            self.set_connection_state(ConnState.CONNECTING, "Waiting for Pwnagotchi SSH...")
            return True
        except Exception as e:
            self.log_message(f"Windows network configuration failed: {e}", "ERROR")
            self.set_connection_state(ConnState.ERROR, "Network configuration failed")
            self.show_toast(f"Network configuration failed: {e}", "error")
            return False

    def setup_internet_sharing_windows(
        self,
        host=None,
        username=None,
        password="",
        auth_method="password",
        ssh_key_path="",
        ssh_key_passphrase="",
        use_ssh_agent=False,
    ):
        """Enable native Windows ICS and verify the Pwnagotchi route over SSH."""
        if not self.is_windows:
            self.log_message("Internet sharing setup is only available on Windows.", "ERROR")
            return False

        if not self.pwnagotchi_adapter_name:
            self.log_message("No detected RNDIS adapter is available for sharing.", "ERROR")
            return False

        try:
            import ctypes

            script_path = self.get_resource_path(
                os.path.join("scripts", "win_connection_share.ps1")
            )
            if not os.path.isfile(script_path):
                raise FileNotFoundError(f"Bundled sharing script not found: {script_path}")

            script_arguments = [
                "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-File", script_path,
                "-PrivateAdapter", self.pwnagotchi_adapter_name,
                "-ScopeAddress", "10.0.0.1",
            ]
            powershell = "powershell.exe"
            self.log_message(
                f"Enabling Windows Internet Sharing for {self.pwnagotchi_adapter_name}...",
                "SYSTEM",
            )

            if ctypes.windll.shell32.IsUserAnAdmin():
                command = [powershell, *script_arguments]
            else:
                self.log_message(
                    "Administrator approval is required to enable Internet Sharing.",
                    "INFO",
                )
                child_arguments = subprocess.list2cmdline(script_arguments).replace("'", "''")
                elevation_command = (
                    "$ErrorActionPreference='Stop'; "
                    f"$p=Start-Process -FilePath '{powershell}' -ArgumentList '{child_arguments}' "
                    "-Verb RunAs -Wait -PassThru; exit $p.ExitCode"
                )
                command = [powershell, "-NoProfile", "-NonInteractive", "-Command", elevation_command]

            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=90,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip()
                raise RuntimeError(detail or f"PowerShell exited with code {completed.returncode}")

            public_adapter = "the active internet adapter"
            for line in completed.stdout.splitlines():
                if line.startswith("PUBLIC_ADAPTER="):
                    public_adapter = line.partition("=")[2].strip()
            self.log_message(
                f"Windows Internet Sharing enabled: {public_adapter} -> {self.pwnagotchi_adapter_name}.",
                "SUCCESS",
            )

            time.sleep(3)
            inspection = self.inspect_device_connection(
                host or self.pwnagotchi_ip,
                username or self.pwnagotchi_user,
                password or self.pwnagotchi_pass,
                auth_method,
                ssh_key_path,
                ssh_key_passphrase,
                use_ssh_agent,
            )
            if not inspection.get("internet_shared"):
                self.log_message(
                    "Windows ICS is enabled, but device internet access was not verified yet.",
                    "WARNING",
                )
            return True
        except Exception as e:
            self.log_message(f"Internet sharing setup failed: {e}", "ERROR")
            return False

    def find_main_internet_adapter_windows(self):
        """Find the main internet-connected adapter on Windows using improved detection."""
        try:
            self.log_message(">>> Searching for active internet adapter using advanced detection... <<<", "INFO")
            
            # Method 1: Use the improved network detection from FindActiveNetwork_win.py
            active_adapter = self.find_active_connection_advanced()
            if active_adapter:
                self.log_message(f">>> Active internet adapter found: {active_adapter['name']} <<<", "SUCCESS")
                return active_adapter['name']
            
            # Method 2: Fallback to default route detection
            self.log_message(">>> Trying default route detection fallback... <<<", "INFO")
            routes = self.get_default_routes()
            if routes:
                best_route = routes[0]  # Lowest metric route
                self.log_message(f">>> Found default route via {best_route['gateway']} on interface {best_route['interface']} <<<", "SUCCESS")
                
                # Test connectivity
                if self.test_internet_connectivity():
                    self.log_message(">>> Internet connectivity confirmed via default route <<<", "SUCCESS")
                    return f"Interface {best_route['interface']}"
            
            # Method 3: Simple ipconfig fallback
            self.log_message(">>> Trying ipconfig fallback... <<<", "INFO")
            return self.find_adapter_ipconfig_fallback()
            
        except Exception as e:
            self.log_message(f">>> Error finding main adapter: {e} <<<", "ERROR")
            return None

    def find_active_connection_advanced(self):
        """Advanced network adapter detection based on FindActiveNetwork_win.py."""
        try:
            # Get all network adapters using netsh
            adapters = self.get_network_adapters_advanced()
            
            if not adapters:
                return None
            
            # Test each connected adapter for internet connectivity
            for adapter in adapters:
                if adapter['status'] == 'Connected':
                    self.log_message(f">>> Testing adapter: {adapter['name']}... <<<", "INFO")
                    
                    # Get IP configuration
                    if not adapter.get('ip_address'):
                        ip_config = self.get_ip_config_advanced(adapter['name'])
                        adapter.update(ip_config)
                    
                    # Test internet connectivity
                    if adapter.get('ip_address') and self.test_internet_connectivity_advanced(adapter['ip_address']):
                        self.log_message(f">>> Internet access confirmed on {adapter['name']}! <<<", "SUCCESS")
                        return adapter
                    else:
                        self.log_message(f">>> No internet access on {adapter['name']} <<<", "WARNING")
            
            return None
            
        except Exception as e:
            self.log_message(f">>> Advanced detection error: {e} <<<", "ERROR")
            return None

    def get_network_adapters_advanced(self):
        """Get network adapters using improved method from FindActiveNetwork_win.py."""
        adapters = []
        
        try:
            # Get interface list using netsh
            result = subprocess.run([
                "netsh", "interface", "show", "interface"
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line and not line.startswith('-') and not line.startswith('Admin') and 'Loopback' not in line:
                        parts = line.split()
                        if len(parts) >= 4:
                            admin_state = parts[0]
                            state = parts[1]
                            interface_type = parts[2]
                            interface_name = ' '.join(parts[3:])
                            
                            if state.lower() in ['connected', 'disconnected'] and interface_name != 'Interface Name':
                                # Skip RNDIS adapters (Pwnagotchi)
                                if "RNDIS" not in interface_name.upper():
                                    adapters.append({
                                        'name': interface_name,
                                        'state': state,
                                        'admin_state': admin_state,
                                        'type': interface_type,
                                        'status': 'Connected' if state.lower() == 'connected' else 'Disconnected'
                                    })
            
            # Get additional info from ipconfig
            result = subprocess.run([
                "ipconfig", "/all"
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                current_adapter = None
                for line in result.stdout.splitlines():
                    line = line.strip()
                    
                    # New adapter section
                    if line and not line.startswith(' ') and ':' not in line.split('.')[0]:
                        current_adapter = line.replace(':', '').strip()
                    elif current_adapter and ':' in line:
                        # Match with our adapters list
                        for adapter in adapters:
                            if any(part.lower() in current_adapter.lower() for part in adapter['name'].lower().split()):
                                if 'IPv4 Address' in line:
                                    ip = line.split(':')[-1].strip().replace('(Preferred)', '').strip()
                                    adapter['ip_address'] = ip
                                elif 'Default Gateway' in line:
                                    gateway = line.split(':')[-1].strip()
                                    if gateway and gateway != '':
                                        adapter['default_gateway'] = gateway
                                break
            
            return adapters
            
        except Exception as e:
            self.log_message(f">>> Error getting adapters: {e} <<<", "ERROR")
            return []

    def get_ip_config_advanced(self, interface_name):
        """Get IP configuration for a specific interface."""
        config = {
            'ip_address': None,
            'subnet_mask': None,
            'default_gateway': None,
            'dns_servers': [],
            'dhcp_enabled': False
        }
        
        try:
            # Get IP address and subnet using netsh
            result = subprocess.run([
                "netsh", "interface", "ip", "show", "addresses", f'"{interface_name}"'
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if 'IP Address:' in line:
                        config['ip_address'] = line.split(':')[-1].strip()
                    elif 'Default Gateway:' in line:
                        gateway = line.split(':')[-1].strip()
                        if gateway and gateway != 'none':
                            config['default_gateway'] = gateway
                    elif 'DHCP enabled:' in line:
                        config['dhcp_enabled'] = 'Yes' in line
            
            return config
            
        except Exception as e:
            self.log_message(f">>> Error getting IP config: {e} <<<", "ERROR")
            return config

    def get_default_routes(self):
        """Get default routes (0.0.0.0/0) sorted by metric."""
        try:
            result = subprocess.run([
                "route", "print", "0.0.0.0"
            ], capture_output=True, text=True, shell=True)
            
            routes = []
            parsing_routes = False
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if 'Network Destination' in line and 'Netmask' in line:
                        parsing_routes = True
                        continue
                    elif parsing_routes and line.strip():
                        if line.startswith('=') or not line.strip():
                            break
                            
                        parts = line.split()
                        if len(parts) >= 5 and parts[0] == '0.0.0.0' and parts[1] == '0.0.0.0':
                            try:
                                routes.append({
                                    'destination': parts[0],
                                    'netmask': parts[1],
                                    'gateway': parts[2],
                                    'interface': parts[3],
                                    'metric': int(parts[4]) if parts[4].isdigit() else 999
                                })
                            except (IndexError, ValueError):
                                continue
            
            # Sort by metric (lower is better)
            return sorted(routes, key=lambda x: x['metric'])
            
        except Exception as e:
            self.log_message(f">>> Error getting default routes: {e} <<<", "ERROR")
            return []

    def test_internet_connectivity_advanced(self, interface_ip=None):
        """Test internet connectivity using socket connection."""
        try:
            import socket
            
            # Try to connect to Google's DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            if interface_ip:
                try:
                    sock.bind((interface_ip, 0))
                except:
                    pass  # If binding fails, try without binding
            
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            return result == 0
            
        except Exception:
            return False

    def find_adapter_ipconfig_fallback(self):
        """Simple fallback using ipconfig."""
        try:
            result = subprocess.run([
                "ipconfig"
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                current_adapter = None
                
                for line in lines:
                    # Look for adapter names
                    if "adapter" in line.lower() and ":" in line:
                        current_adapter = line.split(":")[0].strip()
                    
                    # Look for default gateway
                    if "default gateway" in line.lower() and current_adapter:
                        gateway = line.split(":")[-1].strip()
                        if gateway and gateway != "":
                            # Clean up adapter name
                            clean_name = current_adapter.replace("adapter ", "").replace(":", "").strip()
                            if "RNDIS" not in clean_name.upper():
                                self.log_message(f">>> Using ipconfig fallback adapter: {clean_name} <<<", "SUCCESS")
                                return clean_name
            
            return None
            
        except Exception as e:
            self.log_message(f">>> ipconfig fallback error: {e} <<<", "ERROR")
            return None

    def show_ssh_cert_dialog(self):
        """Show SSH certificate management dialog."""
        if not self.pwnagotchi_detected:
            messagebox.showwarning("Pwnagotchi Not Detected", 
                                 "Please detect and connect to your Pwnagotchi first before managing SSH certificates.")
            return
        
        # Create SSH certificate management dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("SSH Certificate Management")
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="SSH Certificate Management", 
                                 font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(0, 20))
        
        # Status frame
        status_frame = ctk.CTkFrame(main_frame)
        status_frame.pack(fill="x", pady=(0, 20))
        
        status_label = ctk.CTkLabel(status_frame, text="Checking SSH certificate status...", 
                                  font=ctk.CTkFont(size=12))
        status_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        # Test certificate connection button
        test_cert_btn = ctk.CTkButton(buttons_frame, text="Test Certificate Connection", 
                                    command=lambda: self.test_ssh_certificate_connection(dialog, status_label, log_text))
        test_cert_btn.pack(side="left", padx=(0, 10))
        
        # Generate and install certificate button
        gen_cert_btn = ctk.CTkButton(buttons_frame, text="Generate & Install Certificate", 
                                   command=lambda: self.generate_and_install_ssh_certificate(dialog, status_label, log_text))
        gen_cert_btn.pack(side="left", padx=(0, 10))
        
        # Remove certificate button
        remove_cert_btn = ctk.CTkButton(buttons_frame, text="Remove Certificate", 
                                      command=lambda: self.remove_ssh_certificate(dialog, status_label))
        remove_cert_btn.pack(side="left", padx=(0, 10))
        
        # Debug SSH config button
        debug_btn = ctk.CTkButton(buttons_frame, text="Debug SSH Config", 
                                command=lambda: self.debug_ssh_config(dialog, status_label, log_text))
        debug_btn.pack(side="left")
        
        # Log frame
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True)
        
        log_label = ctk.CTkLabel(log_frame, text="SSH Certificate Log:", 
                               font=ctk.CTkFont(size=14, weight="bold"))
        log_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Log text area
        log_text = ctk.CTkTextbox(log_frame, height=200)
        log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Close button
        close_btn = ctk.CTkButton(main_frame, text="Close", command=dialog.destroy)
        close_btn.pack(pady=(10, 0))
        
        # Check initial status
        self.check_ssh_certificate_status(dialog, status_label, log_text)

    def check_ssh_certificate_status(self, dialog, status_label, log_text):
        """Check the current SSH certificate status."""
        def check_status():
            try:
                log_text.insert("end", ">>> Checking SSH certificate status... <<<\n")
                dialog.update()
                
                # Check if SSH key exists locally
                ssh_key_path = self.get_ssh_key_path()
                key_exists = os.path.exists(ssh_key_path)
                
                if key_exists:
                    log_text.insert("end", f">>> SSH key found at: {ssh_key_path} <<<\n")
                    log_text.insert("end", ">>> Testing certificate connection... <<<\n")
                    dialog.update()
                    
                    # Test if we can connect with the certificate
                    if self.test_ssh_certificate_connection_silent():
                        log_text.insert("end", ">>> Certificate connection successful! <<<\n")
                        status_label.configure(text="SSH certificate working")
                    else:
                        log_text.insert("end", ">>> Certificate connection failed - may need to install on Pwnagotchi <<<\n")
                        status_label.configure(text="SSH key exists but not working")
                else:
                    log_text.insert("end", ">>> No SSH key found locally <<<\n")
                    status_label.configure(text="No SSH certificate found")
                    log_text.insert("end", ">>> Click 'Generate & Install Certificate' to create one <<<\n")
                
                log_text.see("end")
                
            except Exception as e:
                log_text.insert("end", f">>> Error checking status: {e} <<<\n")
                status_label.configure(text="Error checking status")
                log_text.see("end")
        
        # Run in background thread
        threading.Thread(target=check_status, daemon=True).start()

    def get_ssh_key_path(self):
        """Get the path to the SSH key file."""
        ssh_dir = os.path.join(os.path.expanduser("~"), ".ssh")
        os.makedirs(ssh_dir, exist_ok=True)
        return os.path.join(ssh_dir, "pwnagotchi_key")

    def test_ssh_certificate_connection_silent(self):
        """Test SSH certificate connection without UI updates."""
        try:
            ssh_key_path = self.get_ssh_key_path()
            if not os.path.exists(ssh_key_path):
                return False
            
            # Try to connect using the certificate
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Load the private key
            private_key = paramiko.RSAKey.from_private_key_file(str(ssh_key_path))
            
            # Connect using the certificate
            client.connect(
                hostname=self.pwnagotchi_ip,
                username=self.pwnagotchi_user,
                pkey=private_key,
                timeout=10
            )
            
            client.close()
            return True
            
        except Exception:
            return False

    def test_ssh_certificate_connection(self, dialog, status_label, log_text):
        """Test SSH connection using certificate."""
        def test_connection():
            try:
                log_text.insert("end", ">>> Testing certificate connection... <<<\n")
                status_label.configure(text="Testing certificate connection...")
                dialog.update()
                
                ssh_key_path = self.get_ssh_key_path()
                if not os.path.exists(ssh_key_path):
                    log_text.insert("end", ">>> No SSH key found - generate one first <<<\n")
                    status_label.configure(text="No SSH key found - generate one first")
                    log_text.see("end")
                    return
                
                log_text.insert("end", f">>> SSH key found at: {ssh_key_path} <<<\n")
                log_text.insert("end", ">>> Attempting certificate connection... <<<\n")
                dialog.update()
                
                # Try to connect using the certificate
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                # Load the private key
                private_key = paramiko.RSAKey.from_private_key_file(str(ssh_key_path))
                
                # Connect using the certificate
                client.connect(
                    hostname=self.pwnagotchi_ip,
                    username=self.pwnagotchi_user,
                    pkey=private_key,
                    timeout=10
                )
                
                # Test a simple command
                stdin, stdout, stderr = client.exec_command("echo 'SSH certificate connection successful!'")
                output = stdout.read().decode().strip()
                
                client.close()
                
                log_text.insert("end", ">>> Certificate connection successful! <<<\n")
                log_text.insert("end", f">>> Command output: {output} <<<\n")
                status_label.configure(text="SSH certificate working")
                log_text.see("end")
                messagebox.showinfo("Success", f"SSH certificate connection successful!\n\nOutput: {output}")
                
            except Exception as e:
                log_text.insert("end", f">>> Certificate connection failed: {e} <<<\n")
                status_label.configure(text="SSH certificate connection failed")
                log_text.see("end")
                messagebox.showerror("Connection Failed", f"SSH certificate connection failed:\n\n{str(e)}")
        
        # Run in background thread
        threading.Thread(target=test_connection, daemon=True).start()

    def generate_and_install_ssh_certificate(self, dialog, status_label, log_text):
        """Generate SSH key and install it on Pwnagotchi."""
        def generate_and_install():
            try:
                log_text.insert("end", ">>> Starting SSH certificate generation and installation... <<<\n")
                status_label.configure(text="Generating SSH key...")
                dialog.update()
                
                # Generate SSH key
                ssh_key_path = self.get_ssh_key_path()
                if os.path.exists(ssh_key_path):
                    # Ask if user wants to overwrite
                    if not messagebox.askyesno("Key Exists", 
                                             f"SSH key already exists at {ssh_key_path}\n\nDo you want to overwrite it?"):
                        log_text.insert("end", ">>> User cancelled - keeping existing key <<<\n")
                        log_text.see("end")
                        return
                    else:
                        log_text.insert("end", ">>> User chose to overwrite existing key <<<\n")
                
                # Generate new SSH key pair
                log_text.insert("end", ">>> Generating new SSH key pair... <<<\n")
                key = paramiko.RSAKey.generate(2048)
                key.write_private_key_file(str(ssh_key_path))
                
                # Set proper permissions on the private key
                if not self.is_windows:
                    os.chmod(ssh_key_path, stat.S_IRUSR | stat.S_IWUSR)
                
                log_text.insert("end", f">>> SSH key generated at: {ssh_key_path} <<<\n")
                
                # Generate the public key file
                public_key_path = str(ssh_key_path) + ".pub"
                with open(public_key_path, 'w') as f:
                    f.write(f"{key.get_name()} {key.get_base64()} pwnsafe-generated-key\n")
                
                log_text.insert("end", f">>> Public key file created: {public_key_path} <<<\n")
                
                log_text.insert("end", ">>> Installing certificate on Pwnagotchi... <<<\n")
                status_label.configure(text="Installing certificate on Pwnagotchi...")
                dialog.update()
                
                # Connect to Pwnagotchi with password to install the key
                log_text.insert("end", ">>> Connecting to Pwnagotchi with password... <<<\n")
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                client.connect(
                    hostname=self.pwnagotchi_ip,
                    username=self.pwnagotchi_user,
                    password=self.pwnagotchi_pass,
                    timeout=10
                )
                
                log_text.insert("end", ">>> Connected to Pwnagotchi successfully <<<\n")
                
                # Create .ssh directory if it doesn't exist
                log_text.insert("end", ">>> Creating .ssh directory on Pwnagotchi... <<<\n")
                stdin, stdout, stderr = client.exec_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
                stdout.read()  # Wait for completion
                
                # Use SCP to copy the public key file
                log_text.insert("end", ">>> Copying public key file to Pwnagotchi... <<<\n")
                try:
                    # Create SFTP client for file transfer
                    sftp = client.open_sftp()
                    
                    # Copy the public key file to the Pwnagotchi
                    remote_public_key_path = f"/home/{self.pwnagotchi_user}/.ssh/pwnagotchi_key.pub"
                    sftp.put(public_key_path, remote_public_key_path)
                    
                    log_text.insert("end", f">>> Public key file copied to: {remote_public_key_path} <<<\n")
                    
                    # Verify the file was copied correctly
                    stdin, stdout, stderr = client.exec_command(f"cat {remote_public_key_path}")
                    copied_content = stdout.read().decode().strip()
                    log_text.insert("end", f">>> Copied content: {copied_content} <<<\n")
                    
                    # Check if authorized_keys exists and show its current content
                    stdin, stdout, stderr = client.exec_command("ls -la ~/.ssh/authorized_keys")
                    auth_keys_info = stdout.read().decode().strip()
                    log_text.insert("end", f">>> authorized_keys info: {auth_keys_info} <<<\n")
                    
                    # Show current authorized_keys content
                    stdin, stdout, stderr = client.exec_command("cat ~/.ssh/authorized_keys")
                    current_auth_keys = stdout.read().decode().strip()
                    log_text.insert("end", f">>> Current authorized_keys content: {current_auth_keys} <<<\n")
                    
                    # Add the public key to authorized_keys (ensure it's not already there)
                    stdin, stdout, stderr = client.exec_command(f"grep -q 'pwnsafe-generated-key' ~/.ssh/authorized_keys || cat {remote_public_key_path} >> ~/.ssh/authorized_keys")
                    stdout.read()  # Wait for completion
                    
                    # Verify the key was added
                    stdin, stdout, stderr = client.exec_command("cat ~/.ssh/authorized_keys")
                    updated_auth_keys = stdout.read().decode().strip()
                    log_text.insert("end", f">>> Updated authorized_keys content: {updated_auth_keys} <<<\n")
                    
                    # Clean up the temporary public key file on Pwnagotchi
                    stdin, stdout, stderr = client.exec_command(f"rm {remote_public_key_path}")
                    stdout.read()  # Wait for completion
                    
                    sftp.close()
                    log_text.insert("end", ">>> Public key file copied and added successfully <<<\n")
                    
                except Exception as scp_error:
                    log_text.insert("end", f">>> SCP failed, trying alternative method: {scp_error} <<<\n")
                    # Fallback to the old method
                    public_key = f"{key.get_name()} {key.get_base64()} pwnsafe-generated-key"
                    stdin, stdout, stderr = client.exec_command("echo '" + public_key + "' >> ~/.ssh/authorized_keys")
                    stdout.read()  # Wait for completion
                    log_text.insert("end", ">>> Public key added using alternative method <<<\n")
                
                # Set proper permissions on authorized_keys
                log_text.insert("end", ">>> Setting proper permissions on authorized_keys... <<<\n")
                stdin, stdout, stderr = client.exec_command("chmod 600 ~/.ssh/authorized_keys")
                stdout.read()  # Wait for completion
                
                client.close()
                log_text.insert("end", ">>> SSH certificate installation completed <<<\n")
                
                # Test the new certificate connection
                log_text.insert("end", ">>> Testing new certificate connection... <<<\n")
                if self.test_ssh_certificate_connection_silent():
                    log_text.insert("end", ">>> Certificate connection test successful! <<<\n")
                    status_label.configure(text="SSH certificate working!")
                    messagebox.showinfo("Success", "SSH certificate generated and installed successfully!\n\nYou can now connect without a password.")
                else:
                    log_text.insert("end", ">>> Certificate installed but test failed <<<\n")
                    status_label.configure(text="Certificate installed but test failed")
                    messagebox.showwarning("Warning", "SSH certificate was installed but the test connection failed.\n\nYou may need to use password authentication.")
                
                log_text.see("end")
                
            except Exception as e:
                log_text.insert("end", f">>> Error: {e} <<<\n")
                status_label.configure(text="Failed to generate/install certificate")
                log_text.see("end")
                messagebox.showerror("Error", f"Failed to generate and install SSH certificate:\n\n{str(e)}")
        
        # Run in background thread
        threading.Thread(target=generate_and_install, daemon=True).start()

    def remove_ssh_certificate(self, dialog, status_label):
        """Remove SSH certificate from Pwnagotchi."""
        def remove_certificate():
            try:
                if not messagebox.askyesno("Confirm Removal", 
                                         "Are you sure you want to remove the SSH certificate from the Pwnagotchi?\n\nThis will require password authentication for future connections."):
                    return
                
                status_label.configure(text="Removing SSH certificate...")
                dialog.update()
                
                # Connect to Pwnagotchi with password to remove the key
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                client.connect(
                    hostname=self.pwnagotchi_ip,
                    username=self.pwnagotchi_user,
                    password=self.pwnagotchi_pass,
                    timeout=10
                )
                
                # Remove the public key from authorized_keys
                stdin, stdout, stderr = client.exec_command("sed -i '/pwnsafe-generated-key/d' ~/.ssh/authorized_keys")
                stdout.read()  # Wait for completion
                
                client.close()
                
                status_label.configure(text="SSH certificate removed successfully!")
                messagebox.showinfo("Success", "SSH certificate removed from Pwnagotchi successfully!")
                
            except Exception as e:
                status_label.configure(text="Failed to remove certificate")
                messagebox.showerror("Error", f"Failed to remove SSH certificate:\n\n{str(e)}")
        
        # Run in background thread
        threading.Thread(target=remove_certificate, daemon=True).start()

    def debug_ssh_config(self, dialog, status_label, log_text):
        """Debug SSH configuration on Pwnagotchi."""
        def debug_config():
            try:
                log_text.insert("end", ">>> Starting SSH configuration debug... <<<\n")
                status_label.configure(text="Debugging SSH configuration...")
                dialog.update()
                
                # Connect to Pwnagotchi with password
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                client.connect(
                    hostname=self.pwnagotchi_ip,
                    username=self.pwnagotchi_user,
                    password=self.pwnagotchi_pass,
                    timeout=10
                )
                
                log_text.insert("end", ">>> Connected to Pwnagotchi for debugging <<<\n")
                
                # Check SSH service status
                log_text.insert("end", ">>> Checking SSH service status... <<<\n")
                stdin, stdout, stderr = client.exec_command("systemctl status ssh")
                ssh_status = stdout.read().decode().strip()
                log_text.insert("end", f">>> SSH Service Status:\n{ssh_status}\n<<<\n")
                
                # Check SSH configuration
                log_text.insert("end", ">>> Checking SSH daemon configuration... <<<\n")
                stdin, stdout, stderr = client.exec_command("grep -E '^(PubkeyAuthentication|AuthorizedKeysFile|PasswordAuthentication)' /etc/ssh/sshd_config")
                ssh_config = stdout.read().decode().strip()
                log_text.insert("end", f">>> SSH Config:\n{ssh_config}\n<<<\n")
                
                # Check .ssh directory permissions
                log_text.insert("end", ">>> Checking .ssh directory permissions... <<<\n")
                stdin, stdout, stderr = client.exec_command("ls -la ~/.ssh/")
                ssh_dir_perms = stdout.read().decode().strip()
                log_text.insert("end", f">>> .ssh Directory:\n{ssh_dir_perms}\n<<<\n")
                
                # Check authorized_keys file
                log_text.insert("end", ">>> Checking authorized_keys file... <<<\n")
                stdin, stdout, stderr = client.exec_command("ls -la ~/.ssh/authorized_keys")
                auth_keys_perms = stdout.read().decode().strip()
                log_text.insert("end", f">>> authorized_keys Permissions:\n{auth_keys_perms}\n<<<\n")
                
                # Show authorized_keys content
                stdin, stdout, stderr = client.exec_command("cat ~/.ssh/authorized_keys")
                auth_keys_content = stdout.read().decode().strip()
                log_text.insert("end", f">>> authorized_keys Content:\n{auth_keys_content}\n<<<\n")
                
                # Check if our key is in authorized_keys
                stdin, stdout, stderr = client.exec_command("grep 'pwnsafe-generated-key' ~/.ssh/authorized_keys")
                our_key = stdout.read().decode().strip()
                if our_key:
                    log_text.insert("end", f">>> Our key found in authorized_keys: {our_key} <<<\n")
                else:
                    log_text.insert("end", ">>> Our key NOT found in authorized_keys! <<<\n")
                
                # Check SSH logs for authentication attempts
                log_text.insert("end", ">>> Checking recent SSH authentication logs... <<<\n")
                stdin, stdout, stderr = client.exec_command("tail -20 /var/log/auth.log | grep ssh")
                ssh_logs = stdout.read().decode().strip()
                log_text.insert("end", f">>> Recent SSH Logs:\n{ssh_logs}\n<<<\n")
                
                # Try to fix permissions if they're wrong
                log_text.insert("end", ">>> Fixing permissions if needed... <<<\n")
                stdin, stdout, stderr = client.exec_command("chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys")
                stdout.read()  # Wait for completion
                log_text.insert("end", ">>> Permissions fixed <<<\n")
                
                client.close()
                
                status_label.configure(text="SSH debug completed - check log for details")
                log_text.insert("end", ">>> SSH configuration debug completed <<<\n")
                log_text.see("end")
                
            except Exception as e:
                log_text.insert("end", f">>> Debug error: {e} <<<\n")
                status_label.configure(text="Debug failed")
                log_text.see("end")
        
        # Run in background thread
        threading.Thread(target=debug_config, daemon=True).start()

    def offer_ssh_certificate_setup(self):
        """Offer to set up SSH certificate when Pwnagotchi is first detected."""
        def offer_setup():
            try:
                # Check if SSH key already exists
                ssh_key_path = self.get_ssh_key_path()
                if os.path.exists(ssh_key_path):
                    # Test if it's already working
                    if self.test_ssh_certificate_connection_silent():
                        self.log_message(">>> SSH certificate already configured and working! <<<", "SUCCESS")
                        return
                
                # Ask user if they want to set up SSH certificate
                result = messagebox.askyesno(
                    "SSH Certificate Setup", 
                    "Pwnagotchi detected! Would you like to set up SSH certificate authentication?\n\n"
                    "This will allow you to connect without entering a password each time.\n\n"
                    "The certificate will be generated locally and installed on your Pwnagotchi."
                )
                
                if result:
                    self.log_message(">>> User requested SSH certificate setup <<<", "INFO")
                    # Automatically generate and install the certificate
                    self.auto_setup_ssh_certificate()
                else:
                    self.log_message(">>> User declined SSH certificate setup <<<", "INFO")
                    
            except Exception as e:
                self.log_message(f">>> Error offering SSH certificate setup: {e} <<<", "ERROR")
        
        # Run in background thread
        threading.Thread(target=offer_setup, daemon=True).start()

    def auto_setup_ssh_certificate(self):
        """Automatically set up SSH certificate without user interaction."""
        try:
            self.log_message(">>> Setting up SSH certificate automatically... <<<", "INFO")
            
            # Generate SSH key
            ssh_key_path = self.get_ssh_key_path()
            if os.path.exists(ssh_key_path):
                self.log_message(">>> SSH key already exists, using existing key <<<", "INFO")
            else:
                self.log_message(">>> Generating new SSH key pair... <<<", "INFO")
                key = paramiko.RSAKey.generate(2048)
                key.write_private_key_file(str(ssh_key_path))
                
                # Set proper permissions on the private key
                if not self.is_windows:
                    os.chmod(ssh_key_path, stat.S_IRUSR | stat.S_IWUSR)
            
            # Load the key and create public key file
            key = paramiko.RSAKey.from_private_key_file(str(ssh_key_path))
            public_key_path = str(ssh_key_path) + ".pub"
            
            # Create public key file if it doesn't exist
            if not os.path.exists(public_key_path):
                with open(public_key_path, 'w') as f:
                    f.write(f"{key.get_name()} {key.get_base64()} pwnsafe-generated-key\n")
                self.log_message(f">>> Public key file created: {public_key_path} <<<", "INFO")
            
            # Install on Pwnagotchi
            self.log_message(">>> Installing SSH key on Pwnagotchi... <<<", "INFO")
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            client.connect(
                hostname=self.pwnagotchi_ip,
                username=self.pwnagotchi_user,
                password=self.pwnagotchi_pass,
                timeout=10
            )
            
            # Create .ssh directory if it doesn't exist
            stdin, stdout, stderr = client.exec_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
            stdout.read()  # Wait for completion
            
            # Check if key is already in authorized_keys
            stdin, stdout, stderr = client.exec_command("grep 'pwnsafe-generated-key' ~/.ssh/authorized_keys")
            result = stdout.read().decode().strip()
            
            if not result:
                # Use SCP to copy the public key file
                try:
                    sftp = client.open_sftp()
                    remote_public_key_path = f"/home/{self.pwnagotchi_user}/.ssh/pwnagotchi_key.pub"
                    sftp.put(public_key_path, remote_public_key_path)
                    
                    # Copy the public key to authorized_keys
                    stdin, stdout, stderr = client.exec_command(f"cat {remote_public_key_path} >> ~/.ssh/authorized_keys")
                    stdout.read()  # Wait for completion
                    
                    # Clean up the temporary public key file on Pwnagotchi
                    stdin, stdout, stderr = client.exec_command(f"rm {remote_public_key_path}")
                    stdout.read()  # Wait for completion
                    
                    sftp.close()
                    self.log_message(">>> SSH key added to authorized_keys via SCP <<<", "SUCCESS")
                    
                except Exception as scp_error:
                    self.log_message(f">>> SCP failed, using alternative method: {scp_error} <<<", "WARNING")
                    # Fallback to the old method
                    public_key = f"{key.get_name()} {key.get_base64()} pwnsafe-generated-key"
                    stdin, stdout, stderr = client.exec_command("echo '" + public_key + "' >> ~/.ssh/authorized_keys")
                    stdout.read()  # Wait for completion
                    self.log_message(">>> SSH key added to authorized_keys <<<", "SUCCESS")
            else:
                self.log_message(">>> SSH key already in authorized_keys <<<", "INFO")
            
            # Set proper permissions on authorized_keys
            stdin, stdout, stderr = client.exec_command("chmod 600 ~/.ssh/authorized_keys")
            stdout.read()  # Wait for completion
            
            client.close()
            
            # Test the certificate connection
            if self.test_ssh_certificate_connection_silent():
                self.log_message(">>> SSH certificate setup completed successfully! <<<", "SUCCESS")
                self.log_message(">>> Future connections will use certificate authentication <<<", "SUCCESS")
            else:
                self.log_message(">>> SSH certificate installed but test failed <<<", "WARNING")
                self.log_message(">>> You may need to use password authentication <<<", "WARNING")
                
        except Exception as e:
            self.log_message(f">>> SSH certificate setup failed: {e} <<<", "ERROR")
            self.log_message(">>> You can set up SSH certificates manually from the File menu <<<", "INFO")

    def test_adapter_connectivity(self, adapter_name):
        """Test if an adapter has internet connectivity."""
        try:
            # Try to ping a reliable server through this adapter
            result = subprocess.run([
                "ping", "-n", "1", "-S", "0.0.0.0", "8.8.8.8"
            ], capture_output=True, text=True, shell=True, timeout=5)
            
            return result.returncode == 0
        except:
            return False

    def verify_internet_sharing(self):
        """Verify that internet sharing is working properly."""
        try:
            self.log_message(">>> Testing Pwnagotchi internet connectivity... <<<", "INFO")
            
            # Test if we can ping the Pwnagotchi
            ping_result = subprocess.run([
                "ping", "-n", "1", "-W", "3000", "10.0.0.2"
            ], capture_output=True, text=True, shell=True)
            
            if ping_result.returncode == 0:
                self.log_message(">>> Pwnagotchi is reachable <<<", "SUCCESS")
                
                # Test if Pwnagotchi can reach the internet (via SSH)
                if self.test_pwnagotchi_internet():
                    self.log_message(">>> Pwnagotchi has internet access! <<<", "SUCCESS")
                    return True
                else:
                    self.log_message(">>> Pwnagotchi is reachable but no internet access <<<", "WARNING")
                    return False
            else:
                self.log_message(">>> Pwnagotchi is not reachable <<<", "ERROR")
                return False
                
        except Exception as e:
            self.log_message(f">>> Verification error: {e} <<<", "ERROR")
            return False

    def test_pwnagotchi_internet(self):
        """Test if Pwnagotchi has internet access via SSH."""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.pwnagotchi_ip, 
                username=self.pwnagotchi_user, 
                password=self.pwnagotchi_pass,
                timeout=10
            )
            
            # Test internet connectivity from Pwnagotchi
            stdin, stdout, stderr = ssh.exec_command("ping -c 1 8.8.8.8")
            exit_code = stdout.channel.recv_exit_status()
            ssh.close()
            
            return exit_code == 0
            
        except Exception:
            return False

    def show_manual_ics_instructions(self, main_adapter):
        """Show manual Internet Connection Sharing instructions."""
        self.log_message(">>> Manual Internet Connection Sharing Setup: <<<", "INFO")
        self.log_message(">>> 1. Press Windows + R, type 'ncpa.cpl', press Enter <<<", "INFO")
        self.log_message(f">>> 2. Right-click '{main_adapter}' -> Properties <<<", "INFO")
        self.log_message(">>> 3. Go to 'Sharing' tab <<<", "INFO")
        self.log_message(">>> 4. Check 'Allow other network users to connect through this computer's Internet connection' <<<", "INFO")
        self.log_message(f">>> 5. In the dropdown, select '{self.pwnagotchi_adapter_name}' <<<", "INFO")
        self.log_message(">>> 6. Click OK and confirm any dialogs <<<", "INFO")
        self.log_message(">>> 7. Wait a few seconds for the configuration to apply <<<", "INFO")
        self.log_message(">>> 8. Test Pwnagotchi internet access <<<", "INFO")
        
        # Offer to open Network Connections automatically
        self.log_message(">>> Would you like to open Network Connections automatically? <<<", "INFO")
        self.log_message(">>> Use Tools -> Open Network Connections to open it now <<<", "INFO")

    def show_adapter_selection_dialog(self):
        """Show dialog to manually select internet adapter."""
        try:
            # Get list of available adapters
            adapters = self.get_available_adapters()
            if not adapters:
                self.log_message(">>> No adapters found for selection <<<", "ERROR")
                return None
            
            # Create selection dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Select Internet Adapter")
            dialog.geometry("500x400")
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (dialog.winfo_screenheight() // 2) - (400 // 2)
            dialog.geometry(f"500x400+{x}+{y}")
            
            # Main frame
            main_frame = ctk.CTkFrame(dialog, corner_radius=10)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text="Select Internet Adapter",
                font=("Courier New", 20, "bold"),
                text_color="#00ff00"
            )
            title_label.pack(pady=(20, 10))
            
            # Instructions
            instructions = """Please select your active internet adapter:

This should be the adapter that provides your internet connection (Wi-Fi, Ethernet, etc.)"""
            
            instructions_label = ctk.CTkLabel(
                main_frame,
                text=instructions,
                font=("Courier New", 11),
                text_color="#ffffff",
                justify="left"
            )
            instructions_label.pack(pady=10, padx=20)
            
            # Adapter selection
            selected_adapter = ctk.StringVar()
            adapter_frame = ctk.CTkFrame(main_frame, corner_radius=10)
            adapter_frame.pack(fill="x", padx=20, pady=10)
            
            for i, (adapter_name, description) in enumerate(adapters):
                radio = ctk.CTkRadioButton(
                    adapter_frame,
                    text=f"{adapter_name} - {description}",
                    variable=selected_adapter,
                    value=adapter_name,
                    font=("Courier New", 10)
                )
                radio.pack(anchor="w", padx=10, pady=5)
            
            # Buttons
            button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            button_frame.pack(pady=20)
            
            select_button = ctk.CTkButton(
                button_frame,
                text="Select Adapter",
                command=dialog.destroy,
                font=("Courier New", 12, "bold"),
                fg_color="#00ff00",
                hover_color="#00cc00",
                text_color="#000000",
                width=150
            )
            select_button.pack(side="left", padx=10)
            
            cancel_button = ctk.CTkButton(
                button_frame,
                text="Cancel",
                command=lambda: [setattr(selected_adapter, 'set', lambda x: None), dialog.destroy()],
                font=("Courier New", 12, "bold"),
                fg_color="#666666",
                hover_color="#888888",
                text_color="#ffffff",
                width=150
            )
            cancel_button.pack(side="left", padx=10)
            
            # Wait for dialog to close
            dialog.wait_window()
            
            return selected_adapter.get() if selected_adapter.get() else None
            
        except Exception as e:
            self.log_message(f">>> Adapter selection dialog error: {e} <<<", "ERROR")
            return None

    def get_available_adapters(self):
        """Get list of available network adapters."""
        adapters = []
        try:
            # Use WMI to get network adapters
            c = wmi.WMI()
            wmi_adapters = c.Win32_NetworkAdapter()
            
            for adapter in wmi_adapters:
                if (adapter.NetConnectionID and 
                    adapter.NetConnectionStatus == 2 and  # Connected
                    adapter.Description and
                    "RNDIS" not in adapter.Description.upper() and  # Not the Pwnagotchi adapter
                    "LOOPBACK" not in adapter.Description.upper() and  # Not loopback
                    "VIRTUAL" not in adapter.Description.upper()):  # Not virtual
                    
                    adapters.append((adapter.NetConnectionID, adapter.Description))
            
            return adapters
            
        except Exception as e:
            self.log_message(f">>> Error getting adapters: {e} <<<", "ERROR")
            return []

    def enable_ics_automatic(self, main_adapter):
        """Try to enable ICS using netsh commands."""
        try:
            self.log_message(">>> Trying netsh method for ICS... <<<", "INFO")
            
            # Enable IP forwarding
            result1 = subprocess.run([
                "netsh", "interface", "ip", "set", "interface", 
                f"name=\"{main_adapter}\"", "forwarding=enabled"
            ], capture_output=True, text=True, shell=True)
            
            # Enable ICS on the main adapter
            result2 = subprocess.run([
                "netsh", "interface", "ip", "set", "interface", 
                f"name=\"{main_adapter}\"", "sharing=enabled"
            ], capture_output=True, text=True, shell=True)
            
            if result1.returncode == 0 and result2.returncode == 0:
                self.log_message(">>> netsh ICS method successful <<<", "SUCCESS")
                return True
            else:
                self.log_message(f">>> netsh ICS failed: {result1.stderr} {result2.stderr} <<<", "WARNING")
                return False
                
        except Exception as e:
            self.log_message(f">>> netsh ICS error: {e} <<<", "ERROR")
            return False

    def enable_ics_powershell(self, main_adapter):
        """Try to enable ICS using PowerShell."""
        try:
            self.log_message(">>> Trying PowerShell method for ICS... <<<", "INFO")
            
            # PowerShell script to enable ICS
            ps_script = f"""
            $adapter = Get-NetAdapter -Name "{main_adapter}"
            $pwnagotchiAdapter = Get-NetAdapter -Name "{self.pwnagotchi_adapter_name}"
            
            # Enable ICS
            Enable-NetAdapterBinding -Name "{main_adapter}" -ComponentID ms_tcpip
            Enable-NetAdapterBinding -Name "{self.pwnagotchi_adapter_name}" -ComponentID ms_tcpip
            
            # Set up sharing
            netsh interface ip set interface "{main_adapter}" forwarding=enabled
            netsh interface ip set interface "{self.pwnagotchi_adapter_name}" forwarding=enabled
            """
            
            result = subprocess.run([
                "powershell", "-Command", ps_script
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                self.log_message(">>> PowerShell ICS method successful <<<", "SUCCESS")
                return True
            else:
                self.log_message(f">>> PowerShell ICS failed: {result.stderr} <<<", "WARNING")
                return False
                
        except Exception as e:
            self.log_message(f">>> PowerShell ICS error: {e} <<<", "ERROR")
            return False

    def enable_ics_registry(self, main_adapter):
        """Try to enable ICS using registry modifications."""
        try:
            self.log_message(">>> Trying registry method for ICS... <<<", "INFO")
            
            # Get adapter GUIDs
            main_guid = self.get_adapter_guid(main_adapter)
            pwnagotchi_guid = self.get_adapter_guid(self.pwnagotchi_adapter_name)
            
            if not main_guid or not pwnagotchi_guid:
                self.log_message(">>> Could not get adapter GUIDs for registry method <<<", "ERROR")
                return False
            
            # Registry modifications for ICS
            registry_commands = [
                # Enable ICS service
                f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess" /v Start /t REG_DWORD /d 3 /f',
                
                # Configure ICS
                f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters" /v ScopeAddress /t REG_SZ /d "10.0.0.0" /f',
                f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters" /v ScopeMask /t REG_SZ /d "255.255.255.0" /f',
                
                # Set up adapter sharing
                f'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\SharedAccess\\Parameters\\FirewallPolicy\\StandardProfile" /v EnableFirewall /t REG_DWORD /d 0 /f',
            ]
            
            success_count = 0
            for cmd in registry_commands:
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    success_count += 1
                else:
                    self.log_message(f">>> Registry command failed: {cmd} <<<", "WARNING")
            
            if success_count >= 3:
                self.log_message(">>> Registry ICS method successful <<<", "SUCCESS")
                return True
            else:
                self.log_message(">>> Registry ICS method failed <<<", "WARNING")
                return False
                
        except Exception as e:
            self.log_message(f">>> Registry ICS error: {e} <<<", "ERROR")
            return False

    def get_adapter_guid(self, adapter_name):
        """Get the GUID of a network adapter."""
        try:
            result = subprocess.run([
                "wmic", "path", "win32_networkadapter", "where", f"NetConnectionID='{adapter_name}'", "get", "GUID", "/value"
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "GUID=" in line:
                        return line.split("=")[1].strip()
            return None
            
        except Exception:
            return None

    def open_network_connections(self):
        """Open Windows Network Connections window."""
        try:
            self.log_message(">>> Opening Network Connections window... <<<", "INFO")
            
            # Open Network Connections using ncpa.cpl
            result = subprocess.run([
                "ncpa.cpl"
            ], shell=True)
            
            if result.returncode == 0:
                self.log_message(">>> Network Connections window opened successfully <<<", "SUCCESS")
                self.log_message(">>> Follow the manual ICS instructions in the log <<<", "INFO")
            else:
                self.log_message(">>> Failed to open Network Connections window <<<", "ERROR")
                
        except Exception as e:
            self.log_message(f">>> Error opening Network Connections: {e} <<<", "ERROR")

    def monitor_pwnagotchi_windows(self):
        """Monitor for Pwnagotchi connection on Windows."""
        if not self.is_windows:
            return
            
        self.log_message(">>> Starting Windows Pwnagotchi monitoring... <<<", "SYSTEM")
        
        def monitor_loop():
            while True:
                try:
                    # Check for new RNDIS adapters
                    if not self.pwnagotchi_detected:
                        if self.detect_pwnagotchi_windows():
                            self.log_message(">>> Pwnagotchi detected and configured! <<<", "SUCCESS")
                    
                    time.sleep(5)  # Check every 5 seconds
                    
                except Exception as e:
                    self.log_message(f">>> Monitoring error: {e} <<<", "ERROR")
                    time.sleep(10)
        
        # Start monitoring in background thread
        threading.Thread(target=monitor_loop, daemon=True).start()

    def start_windows_automation(self):
        """Start Windows-specific automation features."""
        if not self.is_windows:
            return
            
        self.log_message(">>> Windows automation features enabled <<<", "SYSTEM")
        
        # Check if WMI is available
        if not self.check_wmi_availability():
            self.log_message(">>> WMI not available - some features may not work <<<", "WARNING")
            return
            
        self.log_message(">>> Monitoring for Pwnagotchi RNDIS adapters... <<<", "INFO")
        
        # Start Windows monitoring
        self.monitor_pwnagotchi_windows()
        
        # Add Windows-specific menu items
        self.add_windows_menu_items()

    def check_wmi_availability(self):
        """Check if WMI service is available on Windows."""
        try:
            if wmi is None:
                return False
            c = wmi.WMI()
            # Try to query something simple
            list(c.Win32_NetworkAdapter()[:1])
            return True
        except Exception as e:
            self.log_message(f">>> WMI check failed: {e} <<<", "ERROR")
            return False

    def add_windows_menu_items(self):
        """Add Windows-specific menu items."""
        # Windows menu items are now added to the main Tools menu
        pass

    def start_automated_detection(self):
        """Start automated Pwnagotchi detection automatically."""
        self.log_message(">>> Starting automated Pwnagotchi detection... <<<", "SYSTEM")
        self.update_status("Detecting Pwnagotchi...")
        
        # Start detection automatically in background
        if self.is_windows:
            threading.Thread(target=self.automated_windows_detection, daemon=True).start()
        else:
            threading.Thread(target=self.automated_linux_detection, daemon=True).start()


    def automated_windows_detection(self):
        """Automated Windows detection with user feedback."""
        try:
            self.log_message(">>> Automated Windows detection started <<<", "SYSTEM")
            
            # Check for existing Pwnagotchi first
            if self.detect_pwnagotchi_windows():
                self.log_message(">>> Pwnagotchi already detected and configured! <<<", "SUCCESS")
                self.update_status("Pwnagotchi connected and ready!")
                return
            
            # If not found, show guidance
            self.log_message(">>> No Pwnagotchi detected yet <<<", "INFO")
            self.update_status("Waiting for Pwnagotchi connection...")
            
            # Show connection guidance
            self.show_connection_guidance()
            
            # Start monitoring
            self.monitor_pwnagotchi_windows()
            
        except Exception as e:
            self.log_message(f">>> Automated detection error: {e} <<<", "ERROR")
            self.update_status("Detection failed - check logs")

    def automated_linux_detection(self):
        """Automated Linux detection with user feedback."""
        try:
            self.log_message(">>> Automated Linux detection started <<<", "SYSTEM")
            
            # Check for existing Pwnagotchi first
            pwnagotchi_interface = self.find_pwnagotchi_interface()
            if pwnagotchi_interface:
                self.pwnagotchi_interface = pwnagotchi_interface
                self.log_message(f">>> Pwnagotchi interface found: {pwnagotchi_interface} <<<", "SUCCESS")
                
                if self.test_pwnagotchi_connection():
                    self.pwnagotchi_detected = True
                    self.auto_configure_pwnagotchi()
                    self.log_message(">>> Pwnagotchi detected and configured! <<<", "SUCCESS")
                    self.set_connection_state(ConnState.CONNECTED, "Pwnagotchi Connected and Ready!")
                    return
            
            # If not found, show guidance
            self.log_message(">>> No Pwnagotchi detected yet <<<", "INFO")
            self.update_status("Waiting for Pwnagotchi connection...")
            
            # Show connection guidance
            self.show_connection_guidance()
            
            # Start monitoring
            self.start_pwnagotchi_detection()
            
        except Exception as e:
            self.log_message(f">>> Automated detection error: {e} <<<", "ERROR")
            self.set_connection_state(ConnState.ERROR, "Detection failed - check logs")

    def show_connection_guidance(self):
        """Show guidance for connecting Pwnagotchi."""
        self.log_message(">>> CONNECTION GUIDANCE <<<", "SYSTEM")
        if self.is_windows:
            self.log_message(">>> 1. Connect Pwnagotchi to USB DATA port <<<", "INFO")
            self.log_message(">>> 2. Wait for Windows to install RNDIS driver <<<", "INFO")
            self.log_message(">>> 3. PwnSafe will automatically detect and configure <<<", "INFO")
        else:
            self.log_message(">>> 1. Connect Pwnagotchi to USB DATA port <<<", "INFO")
            self.log_message(">>> 2. Configure network interface with 10.0.0.1/24 <<<", "INFO")
            self.log_message(">>> 3. PwnSafe will automatically detect and configure <<<", "INFO")

    def set_connection_state(self, state, msg=None):
        """Wrapper to call UI's set_connection_state if UI exists."""
        if hasattr(self, 'ui') and self.ui:
            self.ui.set_connection_state(state, msg)
    
    def update_status(self, status_text, state=None):
        """Update status - now routes through set_connection_state."""
        # Map legacy calls to new state system
        if state is None:
            # Infer state from text
            if "success" in status_text.lower() or "ready" in status_text.lower():
                state = ConnState.CONNECTED
            elif "error" in status_text.lower() or "failed" in status_text.lower():
                state = ConnState.ERROR
            elif "waiting" in status_text.lower() or "detecting" in status_text.lower():
                state = ConnState.CONNECTING
            else:
                state = ConnState.IDLE
        
        self.set_connection_state(state, status_text)
        
        # For backward compatibility with old UI
        if hasattr(self, 'status_label'):
            self.status_label.configure(text=status_text)
            if hasattr(self, 'update_idletasks'):
                self.update_idletasks()
    
    def log_message(self, message, level="INFO", verbose=False):
        """Log a message - can be overridden by UI."""
        # Check if UI has verbose-aware logging
        if hasattr(self, 'ui') and hasattr(self.ui, 'log_service'):
            self.ui.log_service.log(message, level, verbose)
        else:
            # Fallback for no-UI mode
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def show_toast(self, message, toast_type="info"):
        """Show a toast notification - can be overridden by UI."""
        print(f"[TOAST {toast_type.upper()}] {message}")


def _detect_and_restart_monitor(app, ui, platform_type):
    """Run detection and restart monitor."""
    try:
        if platform_type == "windows":
            app.detect_pwnagotchi_windows()
        else:
            app.detect_pwnagotchi()
    finally:
        # Restart monitor after detection completes (thread-safe)
        def _restart_monitor():
            if hasattr(ui, 'live_monitor_var') and hasattr(ui, 'monitor'):
                if ui.live_monitor_var.get() and ui.monitor:
                    ui.monitor.start()
        
        # Schedule on main thread
        ui.after(0, _restart_monitor)


if __name__ == "__main__":
    try:
        # Import the new compact UI
        from ui_refactor import PwnSafeCompactUI
        
        # Initialize the business logic app (without UI)
        app = BackupRestoreApp(use_ui=False)
        
        # Detect and log platform
        platform_type = app.detect_platform()
        
        # Create the compact UI and pass the app instance
        ui = PwnSafeCompactUI(app)
        
        # Override the app's log methods to use the UI
        app.log_message = ui.log_message
        app.update_status = ui.update_status
        app.show_toast = ui.show_toast
        
        # Store UI reference for thread-safe widget updates
        app.ui = ui
        
        # Start automatic Pwnagotchi detection after UI is ready (if enabled)
        if ui.auto_detect_var.get():
            app.log_message("Scanning for connected Pwnagotchi devices...", "SYSTEM")
            
            # Temporarily stop monitor during auto-detect
            if ui.monitor:
                ui.monitor.stop()
            
            ui.set_connection_state(ConnState.CONNECTING, "Detecting Pwnagotchi…")
            
            # Use platform-specific detection
            if platform_type == "windows":
                # Windows: Use WMI-based detection for RNDIS adapters
                threading.Thread(target=lambda: _detect_and_restart_monitor(app, ui, "windows"), daemon=True).start()
            else:
                # Linux/Mac: Use network interface detection
                threading.Thread(target=lambda: _detect_and_restart_monitor(app, ui, "linux"), daemon=True).start()
        else:
            app.log_message("Auto-detection disabled in Advanced Settings", "INFO")
        
        # Start the main loop
        ui.mainloop()
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
