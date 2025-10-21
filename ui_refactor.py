"""
PwnSafe Compact UI Refactor
Professional, compact desktop utility interface for PwnSafe.
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import platform
import queue
import datetime
from ui_components import CollapsibleSection, StatusBar, ToastNotification, CompactLogViewer
from profile_manager import ProfileManager


class LogService:
    """Thread-safe logging service that uses a queue for cross-thread log messages."""
    
    def __init__(self, ui_append_callable, poll_ms=100):
        self._queue = queue.Queue()
        self._append = ui_append_callable  # Function that appends to text widget
        self._poll_ms = poll_ms
        self._running = False
    
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
    
    def log(self, message, level="INFO"):
        """Thread-safe log method - can be called from any thread."""
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
        self.restore_button_enabled = False
        
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
        self.main_frame.grid_rowconfigure(3, weight=0)  # backup file
        self.main_frame.grid_rowconfigure(4, weight=0)  # primary buttons
        self.main_frame.grid_rowconfigure(5, weight=0)  # advanced settings
        self.main_frame.grid_rowconfigure(6, weight=1, minsize=100)  # SYSTEM LOG expands
        
        # 1. Header Section (60px fixed)
        self._create_header()
        
        # 2. Profile Section (40px fixed)
        self._create_profile_section()
        
        # 3. Connection Section (80px fixed when collapsed)
        self._create_connection_section()
        
        # 4. Backup File Section (50px fixed)
        self._create_backup_section()
        
        # 5. Primary Actions (80px fixed)
        self._create_primary_actions()
        
        # 6. Advanced Settings (CollapsibleSection)
        self._create_advanced_settings()
        
        # 7. System Log (CollapsibleSection)
        self._create_system_log()
        
        # Initialize toast notification system
        self.toast = ToastNotification(self)
        
        # Initialize thread-safe logging service
        self.log_service = LogService(self._append_log_line)
        self.log_service.start(self)
        
        # Log startup message
        self.log_service.log("PwnSafe Compact UI initialized", "SYSTEM")
        self.log_service.log("Ready for operations", "INFO")
    
    def _create_header(self):
        """Create header section with title and status bar."""
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
        
        # Status bar
        self.status_bar = StatusBar(self.header_frame)
        self.status_bar.grid(row=1, column=0, sticky="ew", pady=(self.UNIT, 0))
    
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
        
        # Browse button for SSH key
        self.browse_key_button = ctk.CTkButton(
            connection_grid,
            text="Browse",
            width=60,
            height=self.ENTRY_HEIGHT,
            font=ctk.CTkFont(size=11),
            command=self._browse_ssh_key,
            state="disabled"
        )
        self.browse_key_button.grid(row=1, column=3, padx=0, pady=self.UNIT)
        
        # SSH key path entry (hidden initially)
        self.ssh_key_path = ""
    
    def _create_backup_section(self):
        """Create backup file selection section."""
        self.backup_frame = ctk.CTkFrame(self.main_frame, corner_radius=8)
        self.backup_frame.grid(row=3, column=0, sticky="nsew", pady=(0, self.UNIT))
        
        # Section header
        backup_title = ctk.CTkLabel(
            self.backup_frame,
            text="BACKUP FILE",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors['muted']
        )
        backup_title.pack(pady=(self.PADDING_SECTION, self.UNIT))
        
        # File selection
        file_grid = ctk.CTkFrame(self.backup_frame, fg_color="transparent")
        file_grid.pack(fill="x", padx=self.PADDING_SECTION, pady=(0, self.PADDING_SECTION))
        file_grid.grid_columnconfigure(1, weight=1)
        
        file_label = ctk.CTkLabel(
            file_grid,
            text="File:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['text']
        )
        file_label.grid(row=0, column=0, padx=(0, self.UNIT), pady=self.UNIT, sticky="w")
        
        self.file_entry = ctk.CTkEntry(
            file_grid,
            placeholder_text="Select .tgz backup file...",
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT
        )
        self.file_entry.grid(row=0, column=1, padx=(0, self.UNIT), pady=self.UNIT, sticky="ew")
        self.file_entry.bind("<KeyRelease>", self._on_file_entry_changed)
        
        self.browse_file_button = ctk.CTkButton(
            file_grid,
            text="Browse",
            width=60,
            height=self.ENTRY_HEIGHT,
            font=ctk.CTkFont(size=11),
            command=self._browse_backup_file
        )
        self.browse_file_button.grid(row=0, column=2, padx=0, pady=self.UNIT)
    
    def _create_primary_actions(self):
        """Create primary action buttons."""
        self.actions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.actions_frame.grid(row=4, column=0, sticky="ew", pady=(self.PADDING_LARGE, self.UNIT))
        self.actions_frame.grid_columnconfigure(0, weight=1)
        self.actions_frame.grid_columnconfigure(1, weight=1)
        
        # Button container
        button_container = ctk.CTkFrame(self.actions_frame, fg_color="transparent")
        button_container.grid(row=0, column=0, columnspan=2)
        button_container.grid_columnconfigure(0, weight=1)
        button_container.grid_columnconfigure(1, weight=1)
        
        # Backup button
        self.backup_button = ctk.CTkButton(
            button_container,
            text="Backup Pwnagotchi",
            width=200,
            height=self.BUTTON_HEIGHT,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors['primary'],
            hover_color="#00cc00",
            text_color="#000000",
            command=self._start_backup
        )
        self.backup_button.grid(row=0, column=0, padx=(0, self.PADDING_SECTION), sticky="ew")
        
        # Restore button
        self.restore_button = ctk.CTkButton(
            button_container,
            text="Restore Pwnagotchi",
            width=200,
            height=self.BUTTON_HEIGHT,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.colors['danger'],
            hover_color="#aa0033",
            text_color="#ffffff",
            command=self._start_restore,
            state="disabled"
        )
        self.restore_button.grid(row=0, column=1, sticky="ew")
    
    def _create_advanced_settings(self):
        """Create advanced settings collapsible section."""
        self.advanced_section = CollapsibleSection(
            self.main_frame,
            "ADVANCED SETTINGS",
            is_expanded=False
        )
        self.advanced_section.grid(row=5, column=0, sticky="nsew", pady=(0, self.UNIT))
        
        # Auto-detect toggle
        self.auto_detect_var = ctk.BooleanVar(value=True)
        self.auto_detect_checkbox = ctk.CTkCheckBox(
            self.advanced_section.content_frame,
            text="Auto-detect Pwnagotchi (Windows)",
            variable=self.auto_detect_var,
            command=self._on_auto_detect_changed
        )
        self.advanced_section.add_widget(self.auto_detect_checkbox, pady=self.UNIT)
        
        # Network adapter dropdown (only shown when auto-detect is on)
        self.network_adapter_frame = ctk.CTkFrame(self.advanced_section.content_frame, fg_color="transparent")
        self.advanced_section.add_widget(self.network_adapter_frame, pady=self.UNIT)
        
        adapter_label = ctk.CTkLabel(
            self.network_adapter_frame,
            text="Network Adapter:",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text']
        )
        adapter_label.pack(side="left", padx=(0, self.UNIT))
        
        self.network_adapter_dropdown = ctk.CTkComboBox(
            self.network_adapter_frame,
            values=["Auto-detect"],
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT
        )
        self.network_adapter_dropdown.pack(side="left")
        
        # DNS settings
        dns_frame = ctk.CTkFrame(self.advanced_section.content_frame, fg_color="transparent")
        self.advanced_section.add_widget(dns_frame, pady=self.UNIT)
        
        dns_label = ctk.CTkLabel(
            dns_frame,
            text="DNS:",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text']
        )
        dns_label.pack(side="left", padx=(0, self.UNIT))
        
        self.dns_primary_entry = ctk.CTkEntry(
            dns_frame,
            placeholder_text="Primary DNS",
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT,
            width=120
        )
        self.dns_primary_entry.pack(side="left", padx=(0, self.UNIT))
        
        self.dns_secondary_entry = ctk.CTkEntry(
            dns_frame,
            placeholder_text="Secondary DNS",
            font=ctk.CTkFont(size=11),
            height=self.ENTRY_HEIGHT,
            width=120
        )
        self.dns_secondary_entry.pack(side="left")
    
    def _create_system_log(self):
        """Create system log expandable section with proper grid weights."""
        # Main log frame with grid weights
        self.log_frame = ctk.CTkFrame(self.main_frame, corner_radius=8)
        self.log_frame.grid(row=6, column=0, sticky="nsew", pady=(0, self.UNIT))
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)  # Content row expands
        
        # Header with toggle and buttons
        self.log_header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        self.log_header.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        self.log_header.grid_columnconfigure(1, weight=1)
        
        # Toggle button
        self.log_toggle = ctk.CTkButton(
            self.log_header,
            text="▼ SYSTEM LOG",
            width=120,
            height=24,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color="#333333",
            command=self._toggle_log
        )
        self.log_toggle.grid(row=0, column=0, sticky="w")
        
        # Button container
        self.log_buttons = ctk.CTkFrame(self.log_header, fg_color="transparent")
        self.log_buttons.grid(row=0, column=2, sticky="e")
        
        self.log_clear_btn = ctk.CTkButton(
            self.log_buttons,
            text="Clear",
            width=60,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._clear_log
        )
        self.log_clear_btn.pack(side="left", padx=(0, 4))
        
        self.log_copy_btn = ctk.CTkButton(
            self.log_buttons,
            text="Copy All",
            width=70,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self._copy_log
        )
        self.log_copy_btn.pack(side="left")
        
        # Content frame (collapsible)
        self.log_content = ctk.CTkFrame(self.log_frame, fg_color="#1a1a1a")
        self.log_content.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self.log_content.grid_columnconfigure(0, weight=1)
        self.log_content.grid_rowconfigure(0, weight=1)
        
        # Text widget (no fixed height, properly configured)
        from tkinter import Text
        self.log_text = Text(
            self.log_content,
            font=("Consolas", 10),
            bg="#1a1a1a",
            fg="#E6E6E6",  # Light gray for visibility
            insertbackground="#ffffff",
            selectbackground="#333333",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            wrap="word",
            state="normal"  # Keep normal so we can insert
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        
        # Configure tags for colored output
        self.log_text.tag_configure("success", foreground="#00ff00")
        self.log_text.tag_configure("warning", foreground="#ffff00")
        self.log_text.tag_configure("error", foreground="#ff0000")
        self.log_text.tag_configure("system", foreground="#ff6600")
        self.log_text.tag_configure("info", foreground="#00ff00")
        
        self.log_expanded = True
    
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
    
    def _toggle_log(self):
        """Toggle log panel expansion."""
        self.log_expanded = not self.log_expanded
        if self.log_expanded:
            self.log_content.grid()
            self.log_toggle.configure(text="▼ SYSTEM LOG")
        else:
            self.log_content.grid_remove()
            self.log_toggle.configure(text="▶ SYSTEM LOG")

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
        
        # Advanced settings
        self.auto_detect_var.set(profile.get("auto_detect", True))
        self.dns_primary_entry.delete(0, "end")
        self.dns_primary_entry.insert(0, profile.get("dns_primary", ""))
        self.dns_secondary_entry.delete(0, "end")
        self.dns_secondary_entry.insert(0, profile.get("dns_secondary", ""))
        
        self.current_profile = profile_name
    
    def _on_profile_changed(self, profile_name):
        """Handle profile selection change."""
        self._load_profile_data(profile_name)
        self.profile_manager.set_last_profile(profile_name)
    
    def _on_auth_method_changed(self, auth_method):
        """Handle authentication method change."""
        if auth_method == "SSH Key":
            self.credential_entry.configure(placeholder_text="SSH Key Passphrase", show="")
            self.browse_key_button.configure(state="normal")
        else:
            self.credential_entry.configure(placeholder_text="Password", show="*")
            self.browse_key_button.configure(state="disabled")
    
    def _browse_ssh_key(self):
        """Browse for SSH key file."""
        filename = filedialog.askopenfilename(
            title="Select SSH Key",
            filetypes=[
                ("SSH Keys", "*.pem *.key"),
                ("OpenSSH Keys", "id_rsa id_ed25519"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.ssh_key_path = filename
            self.toast.show_toast(f"SSH key selected: {os.path.basename(filename)}", "success")
    
    def _browse_backup_file(self):
        """Browse for backup file."""
        filename = filedialog.askopenfilename(
            title="Select Backup File",
            filetypes=[("Backup Files", "*.tgz"), ("All Files", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filename)
            self._on_file_entry_changed()
            
            # Save directory for next time
            self.profile_manager.set_last_backup_dir(os.path.dirname(filename))
    
    def _on_file_entry_changed(self, event=None):
        """Handle file entry change."""
        file_path = self.file_entry.get()
        if file_path and os.path.exists(file_path):
            self.restore_button.configure(state="normal")
            self.restore_button_enabled = True
        else:
            self.restore_button.configure(state="disabled")
            self.restore_button_enabled = False
    
    def _on_auto_detect_changed(self):
        """Handle auto-detect toggle change."""
        if self.auto_detect_var.get():
            # Enable network adapter dropdown
            self.network_adapter_dropdown.configure(state="normal")
        else:
            # Disable network adapter dropdown
            self.network_adapter_dropdown.configure(state="disabled")
    
    def _on_enter_pressed(self, event):
        """Handle Enter key press."""
        # If focus is in connection/backup sections, trigger backup
        focused_widget = self.focus_get()
        if focused_widget in [self.host_entry, self.user_entry, self.credential_entry, self.file_entry]:
            if self._validate_inputs():
                self._start_backup()
    
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
    
    def _start_backup(self):
        """Start backup operation."""
        if not self._validate_inputs():
            return
        
        # Update status
        self.status_bar.update_status("Starting backup...", "info")
        self.log_viewer.log_message("Starting backup operation", "SYSTEM")
        
        # Call the main app's backup method
        self.app.start_backup()
    
    def _start_restore(self):
        """Start restore operation."""
        if not self._validate_inputs():
            return
        
        if not self.restore_button_enabled:
            self.toast.show_toast("Please select a backup file first", "error")
            return
        
        # Update status
        self.status_bar.update_status("Starting restore...", "info")
        self.log_viewer.log_message("Starting restore operation", "SYSTEM")
        
        # Call the main app's restore method
        self.app.start_restore()
    
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
            "dns_primary": self.dns_primary_entry.get(),
            "dns_secondary": self.dns_secondary_entry.get(),
            "auto_detect": self.auto_detect_var.get(),
            "network_adapter": self.network_adapter_dropdown.get()
        }
        
        self.profile_manager.save_profile(profile_name, profile_data)
    
    def _on_closing(self):
        """Handle window closing."""
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
    def log_message(self, message, level="INFO"):
        """Log a message to the system log (thread-safe)."""
        self.log_service.log(message, level)
    
    def update_status(self, text, level="info"):
        """Update the status bar."""
        self.status_bar.update_status(text, level)
    
    def show_toast(self, message, toast_type="info"):
        """Show a toast notification."""
        self.toast.show_toast(message, toast_type)
    
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

    def set_password(self, value: str):
        """Set password value (main thread only)."""
        self.password_var.set(value)

    def ui_set_password(self, value: str):
        """Set password value (thread-safe, can be called from worker threads)."""
        self.after(0, lambda: self.set_password(value))
