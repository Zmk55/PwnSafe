"""
PwnSafe UI Components
Reusable UI widgets for the compact PwnSafe interface.
"""

import customtkinter as ctk
from tkinter import Text, Scrollbar
import threading
import time


class CollapsibleSection(ctk.CTkFrame):
    """
    A collapsible section widget with toggle functionality.
    Simple show/hide implementation without animations for v1.
    """
    
    def __init__(self, parent, title, is_expanded=False, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.is_expanded = is_expanded
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header frame with toggle button
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=8, pady=4)
        self.header_frame.grid_columnconfigure(0, weight=0)  # chevron column
        self.header_frame.grid_columnconfigure(1, weight=1)  # title column
        
        # Toggle button (chevron) - ONLY clickable element
        self.toggle_button = ctk.CTkButton(
            self.header_frame,
            text="▾" if is_expanded else "▸",
            width=22,
            height=20,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#333333",
            command=self.toggle
        )
        self.toggle_button.grid(row=0, column=0, sticky="w")
        
        # Section title - NOT clickable
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#888888"
        )
        self.title_label.grid(row=0, column=1, sticky="w", padx=(8, 0))
        
        # Remove any click bindings from title label
        self.title_label.unbind("<Button-1>")
        
        # Content frame (initially hidden)
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid_columnconfigure(0, weight=1)
        if is_expanded:
            self.content_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
    
    def toggle(self):
        """Toggle the expanded state of the section."""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
            self.toggle_button.configure(text="▾")
        else:
            self.content_frame.grid_remove()
            self.toggle_button.configure(text="▸")
    
    def add_widget(self, widget, **pack_options):
        """Add a widget to the content frame."""
        if self.content_frame:
            widget.pack(in_=self.content_frame, **pack_options)
    
    def grid_widget(self, widget, **grid_options):
        """Add a widget to the content frame using grid layout."""
        if self.content_frame:
            widget.grid(in_=self.content_frame, **grid_options)


class StatusBar(ctk.CTkFrame):
    """
    A thin status bar for showing connection and operation status.
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=24, **kwargs)
        self.pack_propagate(False)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self,
            text="Not connected",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.status_label.pack(side="left", padx=8, pady=2)
        
        # Canvas-based indicator dot for precise color control
        self.status_dot = ctk.CTkCanvas(
            self, 
            width=10, 
            height=10, 
            highlightthickness=0,
            bg=self._apply_appearance_mode(self.cget("fg_color"))
        )
        self.status_dot.pack(side="right", padx=8, pady=2)
        self._dot_id = self.status_dot.create_oval(1, 1, 9, 9, fill="#6b7280", outline="")
    
    def update_status(self, text, level="info"):
        """Update the status text and indicator color."""
        self.status_label.configure(text=text)
        
        # Update indicator color based on level
        colors = {
            "info": "#888888",
            "success": "#00aa00", 
            "warning": "#ffaa00",
            "error": "#ff4444",
            "connected": "#00aa00"
        }
        
        color = colors.get(level, "#888888")
        self.status_dot.itemconfig(self._dot_id, fill=color)
    
    def set_state(self, color: str, text: str):
        """Update both dot color and status text."""
        self.status_dot.itemconfig(self._dot_id, fill=color)
        self.status_label.configure(text=text)


class ToastNotification:
    """
    A transient notification system for showing success/error messages.
    Shows small overlay messages that auto-dismiss after 2-3 seconds.
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.toast_window = None
        self.dismiss_timer = None
    
    def show_toast(self, message, toast_type="info", duration=3000):
        """Show a toast notification."""
        # Cancel any existing timer
        if self.dismiss_timer:
            self.parent.after_cancel(self.dismiss_timer)
        
        # Destroy existing toast
        if self.toast_window:
            self.toast_window.destroy()
        
        # Create toast window
        self.toast_window = ctk.CTkToplevel(self.parent)
        self.toast_window.overrideredirect(True)  # Remove window decorations
        self.toast_window.attributes("-topmost", True)
        
        # Position in top-right corner
        self.parent.update_idletasks()
        x = self.parent.winfo_x() + self.parent.winfo_width() - 300
        y = self.parent.winfo_y() + 20
        self.toast_window.geometry(f"280x60+{x}+{y}")
        
        # Toast content
        toast_frame = ctk.CTkFrame(
            self.toast_window,
            corner_radius=8,
            fg_color="#2a2a2a",
            border_width=1,
            border_color="#444444"
        )
        toast_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Icon and message
        icons = {
            "success": "✓",
            "error": "✗", 
            "warning": "⚠",
            "info": "ℹ"
        }
        
        colors = {
            "success": "#00aa00",
            "error": "#ff4444",
            "warning": "#ffaa00", 
            "info": "#4488ff"
        }
        
        icon_label = ctk.CTkLabel(
            toast_frame,
            text=icons.get(toast_type, "ℹ"),
            font=ctk.CTkFont(size=16),
            text_color=colors.get(toast_type, "#4488ff")
        )
        icon_label.pack(side="left", padx=12, pady=8)
        
        message_label = ctk.CTkLabel(
            toast_frame,
            text=message,
            font=ctk.CTkFont(size=11),
            text_color="#ffffff",
            wraplength=200
        )
        message_label.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=8)
        
        # Auto-dismiss timer
        self.dismiss_timer = self.parent.after(duration, self._dismiss_toast)
    
    def _dismiss_toast(self):
        """Dismiss the toast notification."""
        if self.toast_window:
            self.toast_window.destroy()
            self.toast_window = None
        self.dismiss_timer = None


class CompactLogViewer(ctk.CTkFrame):
    """
    A compact log viewer with copy/clear functionality.
    Designed to fit in collapsible sections.
    """
    
    def __init__(self, parent, initial_height=100, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.initial_height = initial_height
        self.is_expanded = False
        
        # Header with controls
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=8, pady=4)
        
        # Copy and Clear buttons
        self.copy_button = ctk.CTkButton(
            self.header_frame,
            text="Copy All",
            width=60,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self.copy_all
        )
        self.copy_button.pack(side="right", padx=(4, 0))
        
        self.clear_button = ctk.CTkButton(
            self.header_frame,
            text="Clear",
            width=60,
            height=24,
            font=ctk.CTkFont(size=10),
            command=self.clear_log
        )
        self.clear_button.pack(side="right")
        
        # Log text area
        self.text_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.text_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        # Text widget with scrollbar
        self.text_widget = Text(
            self.text_frame,
            font=("Consolas", 10),
            bg="#1a1a1a",
            fg="#ffffff",
            insertbackground="#ffffff",
            selectbackground="#333333",
            selectforeground="#ffffff",
            relief="flat",
            borderwidth=0,
            wrap="word",
            height=4  # Initial compact height
        )
        
        # Scrollbar
        self.scrollbar = Scrollbar(
            self.text_frame,
            orient="vertical",
            command=self.text_widget.yview
        )
        self.text_widget.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack text and scrollbar
        self.text_widget.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        self.scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)
        
        # Configure text tags for colors
        self._configure_tags()
    
    def _configure_tags(self):
        """Configure text tags for colored output."""
        self.text_widget.tag_configure("success", foreground="#00ff00")
        self.text_widget.tag_configure("warning", foreground="#ffff00")
        self.text_widget.tag_configure("error", foreground="#ff0000")
        self.text_widget.tag_configure("system", foreground="#ff6600")
        self.text_widget.tag_configure("info", foreground="#00ff00")
    
    def log_message(self, message, level="INFO"):
        """Add a message to the log with cyberpunk styling."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
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
        
        # Insert message and apply color tag
        start_pos = self.text_widget.index("end-1c")
        self.text_widget.insert("end", formatted_msg)
        end_pos = self.text_widget.index("end-1c")
        
        # Apply color based on level
        tag = level.lower() if level.lower() in ["success", "warning", "error", "system"] else "info"
        self.text_widget.tag_add(tag, start_pos, end_pos)
        
        # Auto-scroll to bottom
        self.text_widget.see("end")
    
    def copy_all(self):
        """Copy all log content to clipboard."""
        content = self.text_widget.get("1.0", "end-1c")
        self.text_widget.clipboard_clear()
        self.text_widget.clipboard_append(content)
    
    def clear_log(self):
        """Clear all log content."""
        self.text_widget.delete("1.0", "end")
    
    def set_expanded(self, expanded):
        """Set the expanded state and adjust height accordingly."""
        self.is_expanded = expanded
        if expanded:
            # Calculate 35% of parent window height
            parent_height = self.master.winfo_height()
            target_height = max(200, int(parent_height * 0.35))
            self.text_widget.configure(height=int(target_height / 20))  # Approximate lines
        else:
            self.text_widget.configure(height=4)  # Compact view
