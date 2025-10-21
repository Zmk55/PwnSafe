"""
PwnSafe Profile Manager
Handles profile persistence and management for the compact UI.
"""

import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
import base64


class ProfileManager:
    """
    Manages user profiles with encrypted sensitive data.
    Stores profiles in ~/.pwnsafe/profiles.json (cross-platform).
    """
    
    def __init__(self):
        self.profiles_dir = Path.home() / ".pwnsafe"
        self.profiles_file = self.profiles_dir / "profiles.json"
        self.profiles_data = {}
        self.encryption_key = None
        
        # Create profiles directory if it doesn't exist
        self.profiles_dir.mkdir(exist_ok=True)
        
        # Load or create encryption key
        self._load_or_create_key()
        
        # Load existing profiles
        self.load_profiles()
    
    def _load_or_create_key(self):
        """Load or create encryption key for sensitive data."""
        key_file = self.profiles_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, "rb") as f:
                self.encryption_key = f.read()
        else:
            # Generate new key
            self.encryption_key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(self.encryption_key)
    
    def _encrypt_data(self, data):
        """Encrypt sensitive data."""
        if not data:
            return ""
        
        fernet = Fernet(self.encryption_key)
        encrypted = fernet.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt sensitive data."""
        if not encrypted_data:
            return ""
        
        try:
            fernet = Fernet(self.encryption_key)
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            return ""  # Return empty string if decryption fails
    
    def load_profiles(self):
        """Load profiles from JSON file."""
        if not self.profiles_file.exists():
            self._create_default_profiles()
            return
        
        try:
            with open(self.profiles_file, 'r') as f:
                self.profiles_data = json.load(f)
            
            # Decrypt sensitive fields
            for profile_name, profile in self.profiles_data.get("profiles", {}).items():
                if "ssh_key_passphrase" in profile:
                    profile["ssh_key_passphrase"] = self._decrypt_data(profile["ssh_key_passphrase"])
                    
        except (json.JSONDecodeError, FileNotFoundError):
            self._create_default_profiles()
    
    def _create_default_profiles(self):
        """Create default profile structure."""
        self.profiles_data = {
            "profiles": {
                "Default": {
                    "host": "10.0.0.2",
                    "username": "pi",
                    "auth_method": "password",
                    "ssh_key_path": "",
                    "ssh_key_passphrase": "",
                    "use_ssh_agent": False,
                    "dns_primary": "",
                    "dns_secondary": "",
                    "auto_detect": True,
                    "network_adapter": ""
                }
            },
            "last_profile": "Default",
            "last_backup_dir": "",
            "window_geometry": "900x700+100+100"
        }
        self.save_profiles()
    
    def save_profiles(self):
        """Save profiles to JSON file with encrypted sensitive data."""
        # Create a copy for saving with encrypted sensitive data
        save_data = self.profiles_data.copy()
        
        # Encrypt sensitive fields
        for profile_name, profile in save_data.get("profiles", {}).items():
            if "ssh_key_passphrase" in profile and profile["ssh_key_passphrase"]:
                profile["ssh_key_passphrase"] = self._encrypt_data(profile["ssh_key_passphrase"])
        
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump(save_data, f, indent=2)
        except Exception as e:
            print(f"Error saving profiles: {e}")
    
    def get_profile(self, profile_name):
        """Get a specific profile by name."""
        return self.profiles_data.get("profiles", {}).get(profile_name, {})
    
    def save_profile(self, profile_name, profile_data):
        """Save or update a profile."""
        if "profiles" not in self.profiles_data:
            self.profiles_data["profiles"] = {}
        
        self.profiles_data["profiles"][profile_name] = profile_data.copy()
        self.save_profiles()
    
    def delete_profile(self, profile_name):
        """Delete a profile."""
        if profile_name in self.profiles_data.get("profiles", {}):
            del self.profiles_data["profiles"][profile_name]
            self.save_profiles()
            return True
        return False
    
    def list_profiles(self):
        """Get list of all profile names."""
        return list(self.profiles_data.get("profiles", {}).keys())
    
    def get_last_profile(self):
        """Get the last used profile name."""
        return self.profiles_data.get("last_profile", "Default")
    
    def set_last_profile(self, profile_name):
        """Set the last used profile."""
        self.profiles_data["last_profile"] = profile_name
        self.save_profiles()
    
    def get_window_geometry(self):
        """Get saved window geometry."""
        return self.profiles_data.get("window_geometry", "900x700+100+100")
    
    def set_window_geometry(self, geometry):
        """Save window geometry."""
        self.profiles_data["window_geometry"] = geometry
        self.save_profiles()
    
    def get_last_backup_dir(self):
        """Get last used backup directory."""
        return self.profiles_data.get("last_backup_dir", "")
    
    def set_last_backup_dir(self, directory):
        """Save last used backup directory."""
        self.profiles_data["last_backup_dir"] = directory
        self.save_profiles()
    
    def export_profile(self, profile_name, export_path):
        """Export a profile to a file (for sharing)."""
        profile = self.get_profile(profile_name)
        if not profile:
            return False
        
        # Remove sensitive data for export
        export_profile = profile.copy()
        export_profile.pop("ssh_key_passphrase", None)
        
        try:
            with open(export_path, 'w') as f:
                json.dump(export_profile, f, indent=2)
            return True
        except Exception:
            return False
    
    def import_profile(self, import_path, profile_name):
        """Import a profile from a file."""
        try:
            with open(import_path, 'r') as f:
                profile_data = json.load(f)
            
            # Set default values for missing fields
            default_profile = {
                "host": "10.0.0.2",
                "username": "pi",
                "auth_method": "password",
                "ssh_key_path": "",
                "ssh_key_passphrase": "",
                "use_ssh_agent": False,
                "dns_primary": "",
                "dns_secondary": "",
                "auto_detect": True,
                "network_adapter": ""
            }
            
            # Merge imported data with defaults
            for key, value in default_profile.items():
                if key not in profile_data:
                    profile_data[key] = value
            
            self.save_profile(profile_name, profile_data)
            return True
        except Exception:
            return False
