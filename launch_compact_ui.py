#!/usr/bin/env python3
"""
Simple launcher for PwnSafe Compact UI.
Bypasses the problematic initialization in the main pwnsafe.py file.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the compact UI directly
    from ui_refactor import PwnSafeCompactUI
    
    # Create a minimal business logic class
    class MinimalApp:
        def __init__(self):
            self.is_windows = os.name == 'nt'
            self.pwnagotchi_detected = False
        
        def start_backup(self):
            print("Backup functionality - to be implemented")
        
        def start_restore(self):
            print("Restore functionality - to be implemented")
        
        def log_message(self, message, level="INFO"):
            print(f"[{level}] {message}")
        
        def update_status(self, text, level="info"):
            print(f"Status: {text}")
        
        def show_toast(self, message, toast_type="info"):
            print(f"Toast: {message}")
    
    # Create the minimal app
    app = MinimalApp()
    
    # Create and run the compact UI
    ui = PwnSafeCompactUI(app)
    ui.mainloop()
    
except Exception as e:
    print(f"Error launching compact UI: {e}")
    import traceback
    traceback.print_exc()
