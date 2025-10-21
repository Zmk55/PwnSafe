#!/usr/bin/env python3
"""
PwnSafe Compact UI Launcher
Launches PwnSafe with the new compact, professional interface.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the compact UI
    from ui_refactor import PwnSafeCompactUI
    
    # Create a minimal business logic class
    class PwnSafeBackend:
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
    
    # Create the backend
    backend = PwnSafeBackend()
    
    # Create and run the compact UI
    ui = PwnSafeCompactUI(backend)
    ui.mainloop()
    
except Exception as e:
    print(f"Error launching compact UI: {e}")
    import traceback
    traceback.print_exc()
