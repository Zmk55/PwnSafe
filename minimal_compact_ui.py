#!/usr/bin/env python3
"""
Minimal version of the compact UI to test basic functionality.
"""

import customtkinter as ctk
import sys
import os

class MinimalPwnSafeUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Basic window setup
        self.title("PwnSafe Compact UI - Test")
        self.geometry("600x400")
        self.minsize(500, 300)
        
        # Set dark theme
        ctk.set_appearance_mode("dark")
        
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="PwnSafe v1.0.0 - Compact UI Test",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Status
        status_label = ctk.CTkLabel(
            main_frame,
            text="Status: UI is working!",
            font=ctk.CTkFont(size=12)
        )
        status_label.pack(pady=10)
        
        # Connection section
        conn_frame = ctk.CTkFrame(main_frame)
        conn_frame.pack(fill="x", padx=10, pady=10)
        
        conn_title = ctk.CTkLabel(
            conn_frame,
            text="Connection Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        conn_title.pack(pady=10)
        
        # Host entry
        host_frame = ctk.CTkFrame(conn_frame, fg_color="transparent")
        host_frame.pack(fill="x", padx=10, pady=5)
        
        host_label = ctk.CTkLabel(host_frame, text="Host:")
        host_label.pack(side="left", padx=(0, 10))
        
        self.host_entry = ctk.CTkEntry(host_frame, placeholder_text="10.0.0.2")
        self.host_entry.pack(side="left", fill="x", expand=True)
        
        # User entry
        user_frame = ctk.CTkFrame(conn_frame, fg_color="transparent")
        user_frame.pack(fill="x", padx=10, pady=5)
        
        user_label = ctk.CTkLabel(user_frame, text="User:")
        user_label.pack(side="left", padx=(0, 10))
        
        self.user_entry = ctk.CTkEntry(user_frame, placeholder_text="pi")
        self.user_entry.pack(side="left", fill="x", expand=True)
        
        # Action buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=20)
        
        backup_button = ctk.CTkButton(
            button_frame,
            text="Backup Pwnagotchi",
            height=40,
            fg_color="#00aa00",
            hover_color="#00cc00"
        )
        backup_button.pack(side="left", padx=(0, 10))
        
        restore_button = ctk.CTkButton(
            button_frame,
            text="Restore Pwnagotchi",
            height=40,
            fg_color="#cc0044",
            hover_color="#aa0033"
        )
        restore_button.pack(side="left")
        
        # Test button
        test_button = ctk.CTkButton(
            main_frame,
            text="Test - Close Window",
            command=self.quit
        )
        test_button.pack(pady=20)
        
        print("Minimal compact UI initialized successfully!")

if __name__ == "__main__":
    try:
        print("Starting minimal compact UI test...")
        app = MinimalPwnSafeUI()
        app.mainloop()
        print("Minimal UI test completed.")
    except Exception as e:
        print(f"Error in minimal UI: {e}")
        import traceback
        traceback.print_exc()
