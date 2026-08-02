"""
PwnSafe Compact UI Refactor
Professional, compact desktop utility interface for PwnSafe.
"""

import customtkinter as ctk
from tkinter import Text, filedialog, messagebox, simpledialog
import os
import platform
import queue
import datetime
import re
import threading
from enum import Enum, auto
from ui_components import ToastNotification
from profile_manager import ProfileManager


class ConnState(Enum):
    UNKNOWN = auto()      # grey - not initialized
    IDLE = auto()         # yellow - initial/neutral state  
    CONNECTING = auto()   # yellow - connection attempt in progress
    CONNECTED = auto()    # green - successfully connected/ready
    ERROR = auto()        # red - any error state


class LogService:
    """Thread-safe logging service that uses a queue for cross-thread log messages."""
    
    def __init__(self, ui_append_callable, poll_ms=100):
        self._queue = queue.Queue()
        self._append = ui_append_callable  # Function that appends to text widget
        self._poll_ms = poll_ms
        self._running = False
        self.verbose_mode = False  # Add verbose flag
    
    def start(self, root):
        """Start polling the queue on the main Tk thread."""
        if self._running:
            return
        self._running = True
        
        def _poll():
            try:
                while True:
                    msg_data = self._queue.get_nowait()
                    self._append(msg_data)
            except queue.Empty:
                pass
            if self._running:
                root.after(self._poll_ms, _poll)
        
        root.after(self._poll_ms, _poll)
    
    def stop(self):
        """Stop polling the queue."""
        self._running = False
    
    def set_verbose(self, enabled):
        """Enable/disable verbose logging."""
        self.verbose_mode = enabled
    
    def log(self, message, level="INFO", verbose=False):
        """Thread-safe log method - can be called from any thread.
        
        Args:
            message: Log message text
            level: INFO/WARNING/ERROR/SUCCESS/SYSTEM
            verbose: If True, only log when verbose_mode is enabled
        """
        # Skip verbose messages if verbose mode is off
        if verbose and not self.verbose_mode:
            return
        
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self._queue.put((message, level, timestamp))


class PwnSafeCompactUI(ctk.CTk):
    """
    Compact, professional UI for PwnSafe.
    Replaces the bloated cyberpunk interface with a clean desktop utility layout.
    """
    
    # Spacing constants (8px base unit)
    UNIT = 8
    PADDING_SECTION = 16
    PADDING_LARGE = 24
    BUTTON_HEIGHT = 40
    ENTRY_HEIGHT = 28
    
    def __init__(self, app_instance):
        super().__init__()
        
        # Reference to the main app instance for business logic
        self.app = app_instance
        
        # Initialize profile manager
        self.profile_manager = ProfileManager()
        
        # UI state
        self.current_profile = None
        
        # Connection state tracking
        self._conn_state = ConnState.UNKNOWN
        self._device_inspection_key = None
        self._device_inspection_running = False
        self._sharing_busy = False
        self._active_auth_method = "password"
        self._password_cache = ""
        self._key_passphrase_cache = ""
        self._terminal_client = None
        self._terminal_channel = None
        self._terminal_connecting = False
        self._terminal_stop = threading.Event()
        
        # Monitor state variables
        self.live_monitor_var = ctk.BooleanVar(value=True)
        self.live_interval_var = ctk.IntVar(value=2)
        self.auto_detect_var = ctk.BooleanVar(value=True)
        self.verbose_logging_var = ctk.BooleanVar(value=False)
        self.network_adapter_var = ctk.StringVar(value="Auto-detect")
        self.dns_primary_var = ctk.StringVar(value="")
        self.dns_secondary_var = ctk.StringVar(value="")
        self.monitor = None
        
        # Last used directory for backup/restore
        self._last_backup_dir = os.path.expanduser("~")
        
        # Initialize StringVars for all input fields
        self.host_var = ctk.StringVar(value="10.0.0.2")
        self.user_var = ctk.StringVar(value="pi")
        self.password_var = ctk.StringVar(value="")
        
        # Setup window
        self._setup_window()
        
        # Setup theme
        self._setup_theme()
        
        # Create UI components
        self._create_ui()
        
        # Load initial profile
        self._load_initial_profile()
        
        # Setup keyboard bindings
        self._setup_keyboard_bindings()
        
        # Setup window close handler
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _setup_window(self):
        """Setup window properties and geometry."""
        self.title("PwnSafe v1.0.0")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Load saved geometry
        saved_geometry = self.profile_manager.get_window_geometry()
        if saved_geometry:
            self.geometry(saved_geometry)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
    
    def _setup_theme(self):
        """Setup the professional dark theme."""
        ctk.set_appearance_mode("dark")
        
        # Professional color scheme (reduced neon intensity)
        self.colors = {
            'primary': '#00aa00',      # Subtle green
            'secondary': '#4488ff',     # Blue
            'accent': '#ff6600',       # Orange
            'danger': '#cc0044',        # Red
            'warning': '#ffaa00',       # Yellow
            'background': '#1a1a1a',    # Dark background
            'surface': '#2a2a2a',       # Surface color
            'text': '#ffffff',          # White text
            'muted': '#888888'          # Muted text
        }
    
    def _create_ui(self):
        """Create the main UI layout."""
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=self.PADDING_SECTION, pady=self.PADDING_SECTION)
        
        # Configure grid weights
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=0)  # header
        self.main_frame.grid_rowconfigure(1, weight=0)  # profile
        self.main_frame.grid_rowconfigure(2, weight=0)  # connection
        self.main_frame.grid_rowconfigure(3, weight=1, minsize=100)  # SYSTEM LOG expands
        
        # 1. Header Section (60px fixed)
        self._create_header()
        
        # 2. Profile Section (40px fixed)
        self._create_profile_section()
        
        # 3. Connection Section (80px fixed when collapsed)
        self._create_connection_section()
        
        # 4. System Log and embedded terminal
        self._create_bottom_tabs()
        
        # Initialize toast notification system
        self.toast = ToastNotification(self)
        
        # Initialize thread-safe logging service
        self.log_service = LogService(self._append_log_line)
        self.log_service.start(self)
        
        # Add startup log messages
        self.log_service.log("Starting PwnSafe...", "INFO")
        
        # Initialize connection state
        self.set_connection_state(ConnState.IDLE, "Not connected")
        
        # Initialize connection monitor
        from monitor import ConnectionMonitor
        self.monitor = ConnectionMonitor(
            ui=self,
            interval_sec=self.live_interval_var.get(),
            host_ip="10.0.0.2",
            local_ip="10.0.0.1"
        )

        # Start monitor if enabled
        if self.live_monitor_var.get():
            self.monitor.start()
        
        # Log startup message
        self.log_service.log("PwnSafe Compact UI initialized", "SYSTEM")
        self.log_service.log("Ready for operations.", "SUCCESS")
    
    def _create_header(self):
        """Create the title and prominent connected-device hostname."""
        # Header frame
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, self.UNIT))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="PwnSafe v1.0.0",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['primary']
        )
        self.title_label.grid(row=0, column=0)
        
        self.hostname_label = ctk.CTkLabel(
            self.header_frame,
            text="Device hostname: Waiting for connection",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.colors['muted'],
        )
        self.hostname_label.grid(row=1, column=0, pady=(2, 0))
    
    def _create_profile_section(self):
        """Create profile selection section."""
        self.profile_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.profile_frame.grid(row=1, column=0, sticky="ew", pady=(0, self.UNIT))
        self.profile_frame.grid_columnconfigure(1, weight=1)
        
        # Profile controls
        profile_controls = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        profile_controls.grid(row=0, column=0, sticky="ew")
        profile_controls.grid_columnconfigure(1, weight=1)
        
        # Profile label
        profile_label = ctk.CTkLabel(
            profile_controls,
            text="Profile:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['text']
        )
        profile_label.grid(row=0, column=0, padx=(0, self.UNIT), sticky="w")
        
        # Profile dropdown
        self.profile_dropdown = ctk.CTkComboBox(
            profile_controls,
            values=self.profile_manager.list_profiles(),
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT,
            command=self._on_profile_changed
        )
        self.profile_dropdown.grid(row=0, column=1, padx=(0, self.UNIT), sticky="ew")
        
        # Save profile button
        self.save_profile_button = ctk.CTkButton(
            profile_controls,
            text="Save...",
            width=60,
            height=self.ENTRY_HEIGHT,
            font=ctk.CTkFont(size=11),
            command=self._save_current_profile
        )
        self.save_profile_button.grid(row=0, column=2, sticky="e")
    
    def _create_connection_section(self):
        """Create connection settings section."""
        self.connection_frame = ctk.CTkFrame(self.main_frame, corner_radius=8)
        self.connection_frame.grid(row=2, column=0, sticky="nsew", pady=(0, self.UNIT))
        
        # Section header
        connection_title = ctk.CTkLabel(
            self.connection_frame,
            text="CONNECTION",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors['muted']
        )
        connection_title.pack(pady=(self.PADDING_SECTION, self.UNIT))
        
        # Connection grid
        connection_grid = ctk.CTkFrame(self.connection_frame, fg_color="transparent")
        connection_grid.pack(fill="x", padx=self.PADDING_SECTION, pady=(0, self.PADDING_SECTION))
        connection_grid.grid_columnconfigure(1, weight=1)
        connection_grid.grid_columnconfigure(3, weight=1)
        connection_grid.grid_columnconfigure(4, weight=0, minsize=140)
        
        # Row 1: Host and User
        host_label = ctk.CTkLabel(
            connection_grid,
            text="Host:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['text']
        )
        host_label.grid(row=0, column=0, padx=(0, self.UNIT), pady=self.UNIT, sticky="w")
        
        self.host_entry = ctk.CTkEntry(
            connection_grid,
            textvariable=self.host_var,
            placeholder_text="10.0.0.2",
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT
        )
        self.host_entry.grid(row=0, column=1, padx=(0, self.PADDING_SECTION), pady=self.UNIT, sticky="ew")
        
        user_label = ctk.CTkLabel(
            connection_grid,
            text="User:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['text']
        )
        user_label.grid(row=0, column=2, padx=(0, self.UNIT), pady=self.UNIT, sticky="w")
        
        self.user_entry = ctk.CTkEntry(
            connection_grid,
            textvariable=self.user_var,
            placeholder_text="pi",
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT
        )
        self.user_entry.grid(row=0, column=3, padx=0, pady=self.UNIT, sticky="ew")
        
        # Row 2: Auth method and credentials
        auth_label = ctk.CTkLabel(
            connection_grid,
            text="Auth:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['text']
        )
        auth_label.grid(row=1, column=0, padx=(0, self.UNIT), pady=self.UNIT, sticky="w")
        
        self.auth_dropdown = ctk.CTkComboBox(
            connection_grid,
            values=["Password", "SSH Key"],
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT,
            command=self._on_auth_method_changed
        )
        self.auth_dropdown.grid(row=1, column=1, padx=(0, self.PADDING_SECTION), pady=self.UNIT, sticky="ew")
        
        # Password/Key entry
        self.credential_entry = ctk.CTkEntry(
            connection_grid,
            textvariable=self.password_var,
            placeholder_text="Password",
            show="*",
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT
        )
        self.credential_entry.grid(row=1, column=2, padx=(0, self.UNIT), pady=self.UNIT, sticky="ew")

        self.key_path_label = ctk.CTkLabel(
            connection_grid,
            text="Key will be configured automatically",
            font=ctk.CTkFont(size=10),
            text_color=self.colors['muted'],
            anchor="w",
        )
        self.key_path_label.grid(row=1, column=2, padx=(0, self.UNIT), pady=self.UNIT, sticky="ew")
        self.key_path_label.grid_remove()

        terminal_buttons = ctk.CTkFrame(connection_grid, fg_color="transparent")
        terminal_buttons.grid(row=1, column=3, padx=0, pady=self.UNIT, sticky="e")

        self.ssh_button = ctk.CTkButton(
            terminal_buttons,
            text="SSH",
            width=64,
            height=self.ENTRY_HEIGHT,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_ssh_click,
            state="disabled",
        )
        self.ssh_button.pack(side="left", padx=(0, 6))

        self.sftp_button = ctk.CTkButton(
            terminal_buttons,
            text="SFTP",
            width=64,
            height=self.ENTRY_HEIGHT,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_sftp_click,
        )
        self.sftp_button.pack(side="left")

        self.internet_sharing_button = ctk.CTkButton(
            terminal_buttons,
            text="Share Internet",
            width=105,
            height=self.ENTRY_HEIGHT,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_internet_sharing_click,
            state="disabled",
        )
        self.internet_sharing_button.pack(side="left", padx=(6, 0))
        
        # SSH key path entry (hidden initially)
        self.ssh_key_path = ""
        
        # Action buttons (Backup/Restore)
        # Backup button (green)
        self.backup_button = ctk.CTkButton(
            connection_grid,
            text="Backup\nPwnagotchi",
            width=130,
            height=50,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#22c55e",  # Green
            hover_color="#16a34a",
            text_color="#000000",
            command=self._on_backup_click,
            state="disabled"
        )
        self.backup_button.grid(row=0, column=4, rowspan=1, padx=(16, 0), pady=(self.UNIT, 4), sticky="new")
        
        # Restore button (red)
        self.restore_button = ctk.CTkButton(
            connection_grid,
            text="Restore\nPwnagotchi",
            width=130,
            height=50,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#ef4444",  # Red
            hover_color="#dc2626",
            text_color="#ffffff",
            command=self._on_restore_click,
            state="disabled"
        )
        self.restore_button.grid(row=1, column=4, rowspan=1, padx=(16, 0), pady=(4, self.UNIT), sticky="new")

        for value in (self.host_var, self.user_var, self.password_var):
            value.trace_add("write", self._on_connection_values_changed)
    
    def _create_bottom_tabs(self):
        """Create the tabbed System Log and embedded Terminal pane."""
        self.bottom_tabs = ctk.CTkTabview(self.main_frame)
        self.bottom_tabs.grid(row=3, column=0, sticky="nsew", pady=(0, self.UNIT))
        self.log_tab = self.bottom_tabs.add("System Log")
        self.terminal_tab = self.bottom_tabs.add("Terminal")

        self.log_tab.grid_rowconfigure(1, weight=1)
        self.log_tab.grid_columnconfigure(0, weight=1)
        
        # Control buttons (top-right)
        controls_frame = ctk.CTkFrame(self.log_tab, fg_color="transparent")
        controls_frame.grid(row=0, column=0, sticky="e", pady=(0, 6))
        
        self.log_clear_btn = ctk.CTkButton(
            controls_frame,
            text="Clear",
            width=70,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._clear_log
        )
        self.log_clear_btn.pack(side="left", padx=(0, 6))
        
        self.log_copy_btn = ctk.CTkButton(
            controls_frame,
            text="Copy All",
            width=90,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._copy_log
        )
        self.log_copy_btn.pack(side="left")
        
        self.log_text = Text(
            self.log_tab,
            font=("Consolas", 10),
            bg="#1a1a1a",
            fg="#E6E6E6",
            insertbackground="#ffffff",
            selectbackground="#333333",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            wrap="word",
            state="normal"
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        
        # Configure color tags
        self.log_text.tag_configure("success", foreground="#00ff00")
        self.log_text.tag_configure("warning", foreground="#ffff00")
        self.log_text.tag_configure("error", foreground="#ff0000")
        self.log_text.tag_configure("system", foreground="#ff6600")
        self.log_text.tag_configure("info", foreground="#00ff00")

        self._create_terminal_tab()

    def _create_terminal_tab(self):
        """Create the embedded interactive SSH terminal widgets."""
        self.terminal_tab.grid_rowconfigure(1, weight=1)
        self.terminal_tab.grid_columnconfigure(0, weight=1)

        terminal_controls = ctk.CTkFrame(self.terminal_tab, fg_color="transparent")
        terminal_controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        terminal_controls.grid_columnconfigure(0, weight=1)

        self.terminal_status_label = ctk.CTkLabel(
            terminal_controls,
            text="Disconnected — click SSH to connect",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['muted'],
            anchor="w",
        )
        self.terminal_status_label.grid(row=0, column=0, sticky="ew")

        self.terminal_clear_button = ctk.CTkButton(
            terminal_controls,
            text="Clear",
            width=70,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._clear_terminal,
        )
        self.terminal_clear_button.grid(row=0, column=1, padx=(6, 0))

        self.terminal_disconnect_button = ctk.CTkButton(
            terminal_controls,
            text="Disconnect",
            width=90,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._disconnect_terminal,
            state="disabled",
        )
        self.terminal_disconnect_button.grid(row=0, column=2, padx=(6, 0))

        self.terminal_text = Text(
            self.terminal_tab,
            font=("Consolas", 10),
            bg="#111111",
            fg="#E6E6E6",
            insertbackground="#ffffff",
            selectbackground="#333333",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            wrap="word",
            state="disabled",
            takefocus=True,
        )
        self.terminal_text.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.terminal_text.bind("<KeyPress>", self._send_terminal_key)
        self.terminal_text.bind("<Control-v>", self._paste_terminal)
        self._append_terminal(
            "Click SSH to connect, then click here and type directly into the remote shell.\n"
        )
    
    def _append_log_line(self, msg_data):
        """Append a log line to the text widget (called from main thread only)."""
        message, level, timestamp = msg_data
        
        # Format message with color
        if level == "ERROR":
            formatted_msg = f"[{timestamp}] ERROR: {message}\n"
            tag = "error"
        elif level == "SUCCESS":
            formatted_msg = f"[{timestamp}] SUCCESS: {message}\n"
            tag = "success"
        elif level == "WARNING":
            formatted_msg = f"[{timestamp}] WARNING: {message}\n"
            tag = "warning"
        elif level == "SYSTEM":
            formatted_msg = f"[{timestamp}] SYSTEM: {message}\n"
            tag = "system"
        else:
            formatted_msg = f"[{timestamp}] {message}\n"
            tag = "info"
        
        # Ensure widget is in normal state
        current_state = self.log_text.cget("state")
        if current_state == "disabled":
            self.log_text.configure(state="normal")
        
        # Insert with color tag
        start_pos = self.log_text.index("end-1c")
        self.log_text.insert("end", formatted_msg)
        end_pos = self.log_text.index("end-1c")
        self.log_text.tag_add(tag, start_pos, end_pos)
        
        # Autoscroll to bottom
        self.log_text.see("end")
        
        # Keep in normal state for future inserts
        # self.log_text.configure(state="disabled")  # Don't disable
    

    def _clear_log(self):
        """Clear log content."""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        # Keep in normal state

    def _copy_log(self):
        """Copy all log content to clipboard."""
        content = self.log_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        # Show feedback
        self.show_toast("Log copied to clipboard", "success")
    
    def _setup_keyboard_bindings(self):
        """Setup keyboard shortcuts."""
        self.bind("<Return>", self._on_enter_pressed)
        self.bind("<Escape>", self._on_escape_pressed)
    
    def _load_initial_profile(self):
        """Load the last used profile."""
        last_profile = self.profile_manager.get_last_profile()
        self.profile_dropdown.set(last_profile)
        self._load_profile_data(last_profile)
    
    def _load_profile_data(self, profile_name):
        """Load profile data into UI fields."""
        profile = self.profile_manager.get_profile(profile_name)
        if not profile:
            return
        
        # Update UI fields
        self.host_entry.delete(0, "end")
        self.host_entry.insert(0, profile.get("host", ""))
        
        self.user_entry.delete(0, "end")
        self.user_entry.insert(0, profile.get("username", ""))
        
        auth_method = profile.get("auth_method", "password")
        self.auth_dropdown.set("Password" if auth_method == "password" else "SSH Key")
        self._on_auth_method_changed(auth_method)
        
        if auth_method == "password":
            self.credential_entry.delete(0, "end")
            self.credential_entry.insert(0, profile.get("password", ""))
        else:
            self.ssh_key_path = profile.get("ssh_key_path", "")
            self.credential_entry.delete(0, "end")
            self.credential_entry.insert(0, profile.get("ssh_key_passphrase", ""))
            self._update_key_path_label()
        
        # Persisted background settings (no longer exposed in the compact UI)
        self.auto_detect_var.set(profile.get("auto_detect", True))
        self.live_monitor_var.set(profile.get("live_monitor", True))
        self.live_interval_var.set(profile.get("monitor_interval", 2))
        self.dns_primary_var.set(profile.get("dns_primary", ""))
        self.dns_secondary_var.set(profile.get("dns_secondary", ""))
        self.network_adapter_var.set(profile.get("network_adapter", "Auto-detect"))
        
        # Load last backup directory
        last_dir = profile.get("last_backup_dir", "")
        if last_dir:
            self._last_backup_dir = os.path.abspath(last_dir)
        
        self.current_profile = profile_name
    
    def _on_profile_changed(self, profile_name):
        """Handle profile selection change."""
        self._load_profile_data(profile_name)
        self.profile_manager.set_last_profile(profile_name)
    
    def _on_auth_method_changed(self, auth_method):
        """Handle authentication method change."""
        current_secret = self.password_var.get()
        if self._active_auth_method == "ssh_key":
            self._key_passphrase_cache = current_secret
        else:
            self._password_cache = current_secret

        new_method = "ssh_key" if auth_method in ("SSH Key", "ssh_key") else "password"
        self._active_auth_method = new_method
        if new_method == "ssh_key":
            self.credential_entry.grid_remove()
            self.key_path_label.grid()
            self.password_var.set(self._key_passphrase_cache)
            self._update_key_path_label()
        else:
            self.key_path_label.grid_remove()
            self.credential_entry.grid()
            self.credential_entry.configure(placeholder_text="Password", show="*")
            self.password_var.set(self._password_cache)
        self._device_inspection_key = None
        self._update_action_buttons()
        self._maybe_start_device_inspection()
    
    def _update_key_path_label(self):
        """Show the configured key or explain that the wizard will create it."""
        if self.ssh_key_path:
            text = f"Key: {os.path.basename(self.ssh_key_path)}"
        else:
            text = "Key will be configured automatically"
        self.key_path_label.configure(text=text)

    def _on_connection_values_changed(self, *_args):
        """Refresh actions and device details when connection input changes."""
        if self._active_auth_method == "ssh_key":
            self._key_passphrase_cache = self.password_var.get()
        else:
            self._password_cache = self.password_var.get()
        self._device_inspection_key = None
        self._update_action_buttons()
        self._maybe_start_device_inspection()

    def _credentials_ready(self, options=None):
        """Return whether the active authentication method has usable input."""
        options = options or self.get_connection_options()
        if not options["host"] or not options["username"]:
            return False
        if options["auth_method"] == "ssh_key":
            return bool(options["ssh_key_path"] and os.path.isfile(options["ssh_key_path"]))
        return bool(options["password"])

    def _update_action_buttons(self):
        """Enable connected actions only when their required input is present."""
        if not hasattr(self, "backup_button"):
            return
        try:
            options = self.get_connection_options()
            connected = self._conn_state == ConnState.CONNECTED
            operation_state = "normal" if connected and self._credentials_ready(options) else "disabled"
            self.backup_button.configure(state=operation_state)
            self.restore_button.configure(state=operation_state)
            self.ssh_button.configure(
                state=(
                    "normal"
                    if connected and options["host"] and options["username"]
                    and not self._terminal_connecting
                    else "disabled"
                )
            )
            sharing_ready = (
                platform.system() == "Windows"
                and not self._sharing_busy
            )
            self.internet_sharing_button.configure(
                state="normal" if sharing_ready else "disabled"
            )
        except Exception as error:
            if hasattr(self, "log_service"):
                self.log_service.log(f"Could not update action buttons: {error}", "WARNING")

    def _on_ssh_click(self):
        """Open an embedded Paramiko shell using the active credentials."""
        try:
            options = self.get_connection_options()
            if not options["host"] or not options["username"]:
                self.show_toast("Enter the host and username first", "error")
                return
            if options["auth_method"] == "password" and not options["password"]:
                self.show_toast("Enter valid SSH credentials first", "error")
                return
            if self._terminal_connecting:
                return

            self._disconnect_terminal(silent=True)
            self._terminal_connecting = True
            self.ssh_button.configure(text="Connecting…", state="disabled")
            self.terminal_status_label.configure(
                text=f'Connecting to {options["username"]}@{options["host"]}…',
                text_color=self.colors['warning'],
            )
            self.bottom_tabs.set("Terminal")
            self._append_terminal(
                f'\nConnecting to {options["username"]}@{options["host"]}…\n'
            )
            threading.Thread(
                target=self._terminal_connect_worker,
                args=(options,),
                daemon=True,
            ).start()
        except Exception as error:
            self._terminal_connecting = False
            self._update_action_buttons()
            self.log_service.log(f"Could not start SSH terminal: {error}", "ERROR")
            self.show_toast(f"Could not start SSH terminal: {error}", "error")

    def _terminal_connect_worker(self, options):
        """Authenticate, run the key wizard when needed, and open a PTY shell."""
        client = None
        generated_key_path = ""
        try:
            key_missing = (
                options["auth_method"] == "ssh_key"
                and not os.path.isfile(options["ssh_key_path"])
            )
            if not key_missing:
                client = self.app.ssh_connect(**options)

            if options["auth_method"] == "ssh_key" and not client:
                setup_password = self._request_key_setup_password()
                if setup_password is None:
                    raise RuntimeError("SSH key setup was cancelled")
                if not hasattr(self.app, "setup_ssh_key"):
                    raise RuntimeError("SSH key setup is unavailable")
                generated_key_path = self.app.setup_ssh_key(
                    options["host"],
                    options["username"],
                    setup_password,
                    options["ssh_key_path"],
                )
                options = dict(options)
                options.update(
                    ssh_key_path=generated_key_path,
                    ssh_key_passphrase="",
                    password="",
                )
                client = self.app.ssh_connect(**options)

            if not client:
                raise ConnectionError("SSH authentication failed")
            transport = client.get_transport()
            if transport:
                transport.set_keepalive(30)
            channel = client.invoke_shell(term="xterm", width=120, height=36)
            self.after(
                0,
                lambda: self._terminal_connected(
                    client, channel, options, generated_key_path
                ),
            )
        except Exception as error:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            message = str(error)
            self.after(0, lambda: self._terminal_connection_failed(message))

    def _request_key_setup_password(self):
        """Prompt once on the Tk thread for the password needed to install a key."""
        result = []
        completed = threading.Event()

        def prompt():
            try:
                result.append(
                    simpledialog.askstring(
                        "Set Up SSH Key",
                        "The selected SSH key is missing or invalid.\n\n"
                        "Enter the Pwnagotchi password once. PwnSafe will generate "
                        "a local key and install its public key automatically.",
                        show="*",
                        parent=self,
                    )
                )
            finally:
                completed.set()

        self.after(0, prompt)
        completed.wait()
        return result[0] if result else None

    def _terminal_connected(self, client, channel, options, generated_key_path):
        """Activate a newly authenticated embedded shell on the Tk thread."""
        self._terminal_client = client
        self._terminal_channel = channel
        self._terminal_connecting = False
        self._terminal_stop.clear()
        self.ssh_button.configure(text="SSH")
        self._update_action_buttons()
        self.terminal_disconnect_button.configure(state="normal")
        self.terminal_status_label.configure(
            text=f'Connected to {options["username"]}@{options["host"]}',
            text_color=self.colors['primary'],
        )
        if generated_key_path:
            self.ssh_key_path = os.path.abspath(generated_key_path)
            self._key_passphrase_cache = ""
            self.password_var.set("")
            self._update_key_path_label()
            if self.current_profile:
                self._save_profile_data(self.current_profile)
            self.log_service.log(
                f"SSH key configured and saved: {self.ssh_key_path}", "SUCCESS"
            )
        self.log_service.log("Embedded SSH terminal connected", "SUCCESS")
        self.terminal_text.focus_set()
        threading.Thread(
            target=self._terminal_reader,
            args=(channel,),
            daemon=True,
        ).start()

    def _terminal_connection_failed(self, message):
        """Restore terminal controls after authentication or shell setup fails."""
        self._terminal_connecting = False
        self.ssh_button.configure(text="SSH")
        self._update_action_buttons()
        self.terminal_status_label.configure(
            text="Connection failed",
            text_color=self.colors['danger'],
        )
        self._append_terminal(f"Connection failed: {message}\n")
        self.show_toast(f"SSH terminal failed: {message}", "error")

    def _terminal_reader(self, channel):
        """Forward remote PTY output to the Tk terminal until the channel closes."""
        try:
            while not self._terminal_stop.wait(0.05):
                if channel.recv_ready():
                    data = channel.recv(4096)
                    if not data:
                        break
                    output = data.decode("utf-8", errors="replace")
                    self.after(0, lambda text=output: self._append_terminal(text))
                elif channel.closed or channel.exit_status_ready():
                    break
        except Exception as error:
            message = str(error)
            self.after(0, lambda: self._append_terminal(f"\nTerminal error: {message}\n"))
        finally:
            self.after(0, lambda: self._terminal_session_closed(channel))

    def _terminal_session_closed(self, channel):
        """Mark a remotely closed session without disturbing a newer channel."""
        if channel is not self._terminal_channel:
            return
        self._disconnect_terminal(silent=True)
        self._append_terminal("\nSSH session closed.\n")

    def _disconnect_terminal(self, silent=False):
        """Close the current Paramiko channel/client and reset terminal controls."""
        self._terminal_stop.set()
        channel, client = self._terminal_channel, self._terminal_client
        self._terminal_channel = None
        self._terminal_client = None
        for connection in (channel, client):
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass
        if hasattr(self, "terminal_text"):
            self.terminal_disconnect_button.configure(state="disabled")
            self.terminal_status_label.configure(
                text="Disconnected — click SSH to connect",
                text_color=self.colors['muted'],
            )
        if not silent:
            self._append_terminal("\nDisconnected.\n")

    def _append_terminal(self, text):
        """Append decoded shell output while removing unsupported ANSI controls."""
        clean_text = re.sub(r"\x1b\][^\x07]*(?:\x07|\x1b\\)", "", text)
        clean_text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", clean_text).replace("\r", "")
        self.terminal_text.configure(state="normal")
        self.terminal_text.insert("end", clean_text)
        self.terminal_text.see("end")
        self.terminal_text.configure(state="disabled")

    def _clear_terminal(self):
        """Clear embedded terminal output."""
        self.terminal_text.configure(state="normal")
        self.terminal_text.delete("1.0", "end")
        self.terminal_text.configure(state="disabled")

    def _send_terminal_key(self, event):
        """Forward printable and control keys directly to the remote PTY."""
        if not self._terminal_channel or self._terminal_channel.closed:
            self.show_toast("SSH terminal is not connected", "error")
            return "break"

        special_keys = {
            "Return": "\r",
            "BackSpace": "\x7f",
            "Tab": "\t",
            "Escape": "\x1b",
            "Up": "\x1b[A",
            "Down": "\x1b[B",
            "Right": "\x1b[C",
            "Left": "\x1b[D",
            "Home": "\x1b[H",
            "End": "\x1b[F",
            "Delete": "\x1b[3~",
            "Prior": "\x1b[5~",
            "Next": "\x1b[6~",
        }
        data = special_keys.get(event.keysym, "")
        if event.state & 0x4 and len(event.keysym) == 1 and event.keysym.isalpha():
            data = chr(ord(event.keysym.lower()) - ord("a") + 1)
        elif not data and event.char and event.char.isprintable():
            data = event.char
        if not data:
            return "break"
        try:
            self._terminal_channel.send(data)
        except Exception as error:
            self._append_terminal(f"\nCould not send input: {error}\n")
        return "break"

    def _paste_terminal(self, _event=None):
        """Paste clipboard text into the remote PTY."""
        if self._terminal_channel and not self._terminal_channel.closed:
            try:
                self._terminal_channel.send(self.clipboard_get())
            except Exception as error:
                self._append_terminal(f"\nCould not paste: {error}\n")
        return "break"

    def _on_sftp_click(self):
        """Expose the planned SFTP control without pretending it is implemented."""
        self.log_service.log("SFTP interface is not implemented yet.", "INFO")
        self.show_toast("SFTP interface coming soon", "info")

    def _on_internet_sharing_click(self):
        """Enable Windows ICS without blocking the Tk event loop."""
        try:
            options = self.get_connection_options()
            if platform.system() != "Windows":
                self.show_toast("Internet Sharing setup is only available on Windows", "error")
                return
            if not hasattr(self.app, "setup_internet_sharing_windows"):
                raise RuntimeError("Internet Sharing setup is unavailable")

            self._sharing_busy = True
            self.internet_sharing_button.configure(text="Enabling…", state="disabled")
            self.log_service.log("Starting Windows Internet Sharing setup...", "SYSTEM")
            threading.Thread(
                target=self._internet_sharing_worker,
                args=(options,),
                daemon=True,
            ).start()
        except Exception as error:
            self._sharing_busy = False
            self._update_action_buttons()
            self.log_service.log(f"Could not start Internet Sharing: {error}", "ERROR")
            self.show_toast(f"Could not start Internet Sharing: {error}", "error")

    def _internet_sharing_worker(self, options):
        """Run the elevated backend operation and return its result to Tk."""
        success = False
        try:
            success = bool(self.app.setup_internet_sharing_windows(**options))
        except Exception as error:
            self.log_message(f"Internet Sharing failed: {error}", "ERROR")
        finally:
            self.after(0, lambda: self._finish_internet_sharing(success))

    def _finish_internet_sharing(self, success):
        """Restore the sharing button and notify the user."""
        self._sharing_busy = False
        self.internet_sharing_button.configure(text="Share Internet")
        self._update_action_buttons()
        if success:
            self.show_toast("Internet Sharing enabled", "success")
            self._device_inspection_key = None
            self._maybe_start_device_inspection()
        else:
            self.show_toast("Internet Sharing failed; check the System Log", "error")

    def _connection_fingerprint(self, options):
        """Identify the current target/authentication inputs for one inspection."""
        secret = options["ssh_key_passphrase"] if options["auth_method"] == "ssh_key" else options["password"]
        return (
            options["host"], options["username"], options["auth_method"],
            options["ssh_key_path"], secret,
        )

    def _maybe_start_device_inspection(self):
        """Query hostname and sharing once per connected credential set."""
        if self._conn_state != ConnState.CONNECTED or self._device_inspection_running:
            return
        try:
            options = self.get_connection_options()
            if not self._credentials_ready(options):
                self.hostname_label.configure(
                    text="Device hostname: Enter SSH credentials",
                    text_color=self.colors['warning'],
                )
                return
            fingerprint = self._connection_fingerprint(options)
            if fingerprint == self._device_inspection_key:
                return
            self._device_inspection_key = fingerprint
            self._device_inspection_running = True
            self.hostname_label.configure(
                text="Device hostname: Identifying…",
                text_color=self.colors['warning'],
            )
            threading.Thread(
                target=self._inspect_device_worker,
                args=(options, fingerprint),
                daemon=True,
            ).start()
        except Exception as error:
            self.log_service.log(f"Could not start device inspection: {error}", "WARNING")

    def _inspect_device_worker(self, options, fingerprint):
        """Run the backend device checks away from the Tk thread."""
        result = {}
        try:
            if not hasattr(self.app, "inspect_device_connection"):
                raise RuntimeError("Device inspection is unavailable")
            result = self.app.inspect_device_connection(**options) or {}
        except Exception as error:
            self.log_message(f"Device inspection failed: {error}", "WARNING")
        finally:
            self.after(0, lambda: self._finish_device_inspection(result, fingerprint))

    def _finish_device_inspection(self, result, fingerprint):
        """Apply an inspection result only if the connection inputs still match."""
        self._device_inspection_running = False
        try:
            current_options = self.get_connection_options()
            if fingerprint != self._connection_fingerprint(current_options):
                self._device_inspection_key = None
                self._maybe_start_device_inspection()
                return
            hostname = str(result.get("hostname", "")).strip()
            if hostname:
                self.hostname_label.configure(
                    text=f"Device hostname: {hostname}",
                    text_color=self.colors['primary'],
                )
            else:
                self.hostname_label.configure(
                    text=f'Device hostname: unavailable ({current_options["host"]})',
                    text_color=self.colors['warning'],
                )
        except Exception as error:
            self.log_service.log(f"Could not display device hostname: {error}", "WARNING")
    
    def _on_enter_pressed(self, event):
        """Handle Enter key press."""
        # If focus is in connection/backup sections, trigger backup
        focused_widget = self.focus_get()
        if focused_widget in [self.host_entry, self.user_entry, self.credential_entry]:
            if self._validate_inputs():
                self._on_backup_click()
    
    def _on_escape_pressed(self, event):
        """Handle Escape key press."""
        # Close any open dialogs or collapse sections
        pass
    
    def _validate_inputs(self):
        """Validate required inputs."""
        host = self.host_entry.get().strip()
        user = self.user_entry.get().strip()
        
        if not host or not user:
            self.toast.show_toast("Please enter host and username", "error")
            return False
        
        return True
    
    
    def _save_current_profile(self):
        """Save current settings as a new profile."""
        # This would open a dialog to enter profile name
        # For now, just save to current profile
        self._save_profile_data(self.current_profile)
        self.toast.show_toast("Profile saved", "success")
    
    def _save_profile_data(self, profile_name):
        """Save current UI data to profile."""
        profile_data = {
            "host": self.host_entry.get(),
            "username": self.user_entry.get(),
            "auth_method": "password" if self.auth_dropdown.get() == "Password" else "ssh_key",
            "ssh_key_path": self.ssh_key_path,
            "ssh_key_passphrase": self.credential_entry.get() if self.auth_dropdown.get() == "SSH Key" else "",
            "use_ssh_agent": False,  # TODO: Add checkbox for this
            "dns_primary": self.dns_primary_var.get(),
            "dns_secondary": self.dns_secondary_var.get(),
            "auto_detect": self.auto_detect_var.get(),
            "live_monitor": self.live_monitor_var.get(),
            "monitor_interval": self.live_interval_var.get(),
            "network_adapter": self.network_adapter_var.get(),
            "last_backup_dir": str(self._last_backup_dir)
        }
        
        self.profile_manager.save_profile(profile_name, profile_data)
    
    def _on_closing(self):
        """Handle window closing."""
        self._disconnect_terminal(silent=True)

        # Stop monitor
        if hasattr(self, 'monitor') and self.monitor:
            self.monitor.stop()
        
        # Stop log service
        if hasattr(self, 'log_service'):
            self.log_service.stop()
        
        # Save current profile
        if self.current_profile:
            self._save_profile_data(self.current_profile)
        
        # Save window geometry
        geometry = self.geometry()
        self.profile_manager.set_window_geometry(geometry)
        
        # Close the window
        self.destroy()
    
    # Public methods for the main app to use
    def log_message(self, message, level="INFO", verbose=False):
        """Log a message to the system log (thread-safe)."""
        self.log_service.log(message, level, verbose)
    
    def update_status(self, text, level="info"):
        """Retain legacy status updates without recreating the removed status bar."""
        self._status_text = text
    
    def show_toast(self, message, toast_type="info"):
        """Show a toast notification from either the UI or a worker thread."""
        self.after(0, lambda: self.toast.show_toast(message, toast_type))

    def confirm_rndis_driver_install(self, driver_name):
        """Ask on the Tk thread whether the bundled Windows driver may be installed."""
        def ask():
            return messagebox.askyesno(
                "RNDIS Driver Required",
                f"Windows does not have the required RNDIS driver installed.\n\n"
                f"Install the bundled {driver_name} driver now?\n\n"
                "Windows will request administrator approval.",
                parent=self,
            )

        if threading.current_thread() is threading.main_thread():
            return ask()

        result = []
        completed = threading.Event()

        def ask_on_ui_thread():
            try:
                result.append(ask())
            finally:
                completed.set()

        self.after(0, ask_on_ui_thread)
        completed.wait()
        return bool(result and result[0])
    
    # Thread-safe UI adapter methods for autodetect
    def get_host(self) -> str:
        """Get host value (thread-safe read)."""
        return self.host_var.get()

    def set_host(self, value: str):
        """Set host value (main thread only)."""
        self.host_var.set(value)

    def ui_set_host(self, value: str):
        """Set host value (thread-safe, can be called from worker threads)."""
        self.after(0, lambda: self.set_host(value))

    def get_user(self) -> str:
        """Get user value (thread-safe read)."""
        return self.user_var.get()

    def set_user(self, value: str):
        """Set user value (main thread only)."""
        self.user_var.set(value)

    def ui_set_user(self, value: str):
        """Set user value (thread-safe, can be called from worker threads)."""
        self.after(0, lambda: self.set_user(value))

    def get_password(self) -> str:
        """Get password value (thread-safe read)."""
        return self.password_var.get()

    def get_connection_options(self):
        """Capture all Tk-managed connection values before starting a worker."""
        use_key = self.auth_dropdown.get() == "SSH Key"
        return {
            "host": self.host_entry.get().strip(),
            "username": self.user_entry.get().strip(),
            "password": "" if use_key else self.credential_entry.get(),
            "auth_method": "ssh_key" if use_key else "password",
            "ssh_key_path": self.ssh_key_path if use_key else "",
            "ssh_key_passphrase": self.credential_entry.get() if use_key else "",
            "use_ssh_agent": False,
        }

    def set_password(self, value: str):
        """Set password value (main thread only)."""
        self.password_var.set(value)

    def ui_set_password(self, value: str):
        """Set password value (thread-safe, can be called from worker threads)."""
        self.after(0, lambda: self.set_password(value))
    
    def set_connection_state(self, state: ConnState, msg: str = None):
        """
        Central API for updating connection state.
        Thread-safe: marshals updates to main Tk thread.
        """
        text_map = {
            ConnState.UNKNOWN:    "Not connected",
            ConnState.IDLE:       "Idle",
            ConnState.CONNECTING: "Connecting…",
            ConnState.CONNECTED:  "Pwnagotchi Connected and Ready!",
            ConnState.ERROR:      "Connection error",
        }
        
        status_text = msg if msg is not None else text_map.get(state, "")

        def _apply():
            try:
                self._conn_state = state
                self._status_text = status_text
                self._update_action_buttons()
                if state == ConnState.CONNECTED:
                    self._maybe_start_device_inspection()
                elif state in (ConnState.UNKNOWN, ConnState.IDLE, ConnState.ERROR):
                    self._device_inspection_key = None
                    self.hostname_label.configure(
                        text="Device hostname: Waiting for connection",
                        text_color=self.colors['muted'],
                    )
            except Exception as error:
                if hasattr(self, "log_service"):
                    self.log_service.log(f"Could not update connection state: {error}", "WARNING")
        
        self.after(0, _apply)
    
    def _on_live_monitor_changed(self):
        """Handle live monitor toggle."""
        if self.live_monitor_var.get():
            self.monitor.start()
            self.log_service.log("Live monitoring started", "SYSTEM")
        else:
            self.monitor.stop()
            self.log_service.log("Live monitoring stopped", "SYSTEM")
    
    def _on_verbose_logging_changed(self):
        """Toggle verbose logging mode."""
        enabled = self.verbose_logging_var.get()
        if hasattr(self, 'log_service'):
            self.log_service.set_verbose(enabled)
        status = "enabled" if enabled else "disabled"
        self.log_message(f"Verbose logging {status}", "INFO")

    def _on_interval_changed(self, event=None):
        """Handle monitor interval change."""
        try:
            interval = self.live_interval_var.get()
            if interval < 1:
                self.live_interval_var.set(1)
                interval = 1
            elif interval > 10:
                self.live_interval_var.set(10)
                interval = 10
            
            if self.monitor:
                self.monitor.set_interval(interval)
                self.log_service.log(f"Monitor interval set to {interval}s", "INFO")
        except Exception:
            self.live_interval_var.set(2)
    
    def _default_backup_name(self):
        """Generate default backup filename with timestamp."""
        import time
        ts = time.strftime("%Y%m%d_%H%M%S")
        return f"pwnsafe_backup_{ts}.tgz"

    def _choose_backup_path(self):
        """Open save dialog for backup file."""
        initial_file = self._default_backup_name()
        path = filedialog.asksaveasfilename(
            title="Save backup as...",
            defaultextension=".tgz",
            initialfile=initial_file,
            initialdir=str(self._last_backup_dir),
            filetypes=[("Tar Gzip", "*.tgz"), ("All Files", "*.*")]
        )
        if path:
            self._last_backup_dir = os.path.dirname(os.path.abspath(path))
            return path
        return None

    def _choose_restore_file(self):
        """Open file dialog for restore source."""
        path = filedialog.askopenfilename(
            title="Select backup file to restore...",
            initialdir=str(self._last_backup_dir),
            filetypes=[("Tar Gzip", "*.tgz"), ("All Files", "*.*")]
        )
        if path:
            self._last_backup_dir = os.path.dirname(os.path.abspath(path))
            return path
        return None
    
    def _on_backup_click(self):
        """Handle backup button click."""
        # Check connection state
        if self._conn_state != ConnState.CONNECTED:
            self.show_toast("Not connected to Pwnagotchi", "error")
            return
        
        # Get backup destination path
        dest_path = self._choose_backup_path()
        if not dest_path:
            return  # User cancelled
        
        # Log and start backup
        self.log_service.log(f"Backup destination: {dest_path}", "INFO")
        
        # Save previous state
        self._prev_state = self._conn_state
        
        # Set to connecting during operation
        self.set_connection_state(ConnState.CONNECTING, "Backup in progress…")
        self.log_service.log("Starting backup operation", "SYSTEM")
        
        # Call app's backup method with path
        if hasattr(self.app, 'backup_to_path'):
            self.app.backup_to_path(dest_path, **self.get_connection_options())
        else:
            self.show_toast("Backup function not available", "error")

    def _on_restore_click(self):
        """Handle restore button click."""
        # Check connection state
        if self._conn_state != ConnState.CONNECTED:
            self.show_toast("Not connected to Pwnagotchi", "error")
            return
        
        # Get restore source path
        src_path = self._choose_restore_file()
        if not src_path:
            return  # User cancelled
        
        # Verify file exists
        if not os.path.isfile(src_path):
            self.show_toast("Backup file not found", "error")
            return
        
        # Log and start restore
        self.log_service.log(f"Restore source: {src_path}", "INFO")
        
        # Save previous state
        self._prev_state = self._conn_state
        
        # Set to connecting during operation
        self.set_connection_state(ConnState.CONNECTING, "Restore in progress…")
        self.log_service.log("Starting restore operation", "SYSTEM")
        
        # Call app's restore method with path
        if hasattr(self.app, 'restore_from_path'):
            self.app.restore_from_path(src_path, **self.get_connection_options())
        else:
            self.show_toast("Restore function not available", "error")
