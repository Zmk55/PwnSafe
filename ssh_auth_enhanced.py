"""
Enhanced SSH Authentication for PwnSafe
Supports password, SSH key, and ssh-agent authentication methods.
"""

import paramiko
import os
import stat


class SSHAuthManager:
    """
    Enhanced SSH authentication manager supporting multiple auth methods.
    """
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
    
    def log_message(self, message, level="INFO"):
        """Log a message using the provided callback."""
        if self.log_callback:
            self.log_callback(message, level)
        else:
            print(f"[{level}] {message}")
    
    def connect(self, host, username, auth_method="password", password="", 
                ssh_key_path="", ssh_key_passphrase="", use_ssh_agent=False, timeout=10):
        """
        Connect to SSH host using specified authentication method.
        
        Args:
            host: SSH hostname or IP
            username: SSH username
            auth_method: "password" or "ssh_key"
            password: Password for password auth
            ssh_key_path: Path to SSH private key file
            ssh_key_passphrase: Passphrase for encrypted SSH key
            use_ssh_agent: Try ssh-agent first if True
            timeout: Connection timeout in seconds
        
        Returns:
            paramiko.SSHClient instance if successful, None if failed
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            if auth_method == "ssh_key":
                return self._connect_with_key(
                    ssh, host, username, ssh_key_path, ssh_key_passphrase, 
                    use_ssh_agent, timeout
                )
            else:
                return self._connect_with_password(ssh, host, username, password, timeout)
                
        except Exception as e:
            try:
                ssh.close()
            except Exception:
                pass
            self.log_message(f"SSH Connection Failed: {e}", "ERROR")
            return None
    
    def _connect_with_key(self, ssh, host, username, key_path, passphrase, use_ssh_agent, timeout):
        """Connect using SSH key authentication."""
        
        # Try ssh-agent first if requested
        if use_ssh_agent:
            try:
                self.log_message(">>> Attempting ssh-agent authentication... <<<", "INFO")
                ssh.connect(host, username=username, timeout=timeout)
                self.log_message(">>> SSH-agent authentication successful! <<<", "SUCCESS")
                return ssh
            except Exception as agent_error:
                self.log_message(f">>> SSH-agent failed: {agent_error} <<<", "WARNING")
                self.log_message(">>> Falling back to key file authentication... <<<", "INFO")
        
        # Try key file authentication
        if not key_path or not os.path.exists(key_path):
            self.log_message(">>> SSH key file not found or not specified <<<", "ERROR")
            ssh.close()
            return None
        
        try:
            self.log_message(f">>> Attempting SSH key authentication with {os.path.basename(key_path)}... <<<", "INFO")
            
            # Load the private key
            private_key = self._load_private_key(key_path, passphrase)
            if not private_key:
                return None
            
            # Connect using the private key
            ssh.connect(host, username=username, pkey=private_key, timeout=timeout)
            self.log_message(">>> SSH key authentication successful! <<<", "SUCCESS")
            return ssh
            
        except Exception as key_error:
            ssh.close()
            self.log_message(f">>> SSH key authentication failed: {key_error} <<<", "ERROR")
            return None
    
    def _connect_with_password(self, ssh, host, username, password, timeout):
        """Connect using password authentication."""
        try:
            self.log_message(">>> Attempting password authentication... <<<", "INFO")
            ssh.connect(host, username=username, password=password, timeout=timeout)
            self.log_message(">>> Password authentication successful! <<<", "SUCCESS")
            return ssh
        except Exception as e:
            ssh.close()
            self.log_message(f">>> Password authentication failed: {e} <<<", "ERROR")
            return None
    
    def _load_private_key(self, key_path, passphrase=""):
        """Load private key from file, supporting multiple formats."""
        try:
            # Check file permissions (SSH keys should not be world-readable)
            file_stat = os.stat(key_path)
            if file_stat.st_mode & stat.S_IRWXO:  # World readable
                self.log_message(">>> Warning: SSH key file is world-readable (security risk) <<<", "WARNING")
            
            # Try different key types
            key_types = [
                (paramiko.RSAKey, "RSA"),
                (paramiko.Ed25519Key, "Ed25519"),
                (paramiko.ECDSAKey, "ECDSA"),
            ]
            if hasattr(paramiko, "DSSKey"):
                key_types.append((paramiko.DSSKey, "DSS"))
            
            for key_class, key_name in key_types:
                try:
                    if passphrase:
                        private_key = key_class.from_private_key_file(key_path, password=passphrase)
                    else:
                        private_key = key_class.from_private_key_file(key_path)
                    
                    self.log_message(f">>> Loaded {key_name} private key <<<", "INFO")
                    return private_key
                    
                except paramiko.ssh_exception.PasswordRequiredException:
                    if not passphrase:
                        self.log_message(f">>> {key_name} key requires passphrase <<<", "WARNING")
                        continue
                    else:
                        raise
                except Exception:
                    # Try next key type
                    continue
            
            # If we get here, none of the key types worked
            self.log_message(">>> Failed to load private key - unsupported format or corrupted file <<<", "ERROR")
            return None
            
        except Exception as e:
            self.log_message(f">>> Error loading private key: {e} <<<", "ERROR")
            return None
    
    def validate_key_file(self, key_path):
        """Validate SSH key file format and permissions."""
        if not key_path or not os.path.exists(key_path):
            return False, "Key file does not exist"
        
        try:
            # Check file permissions
            file_stat = os.stat(key_path)
            if file_stat.st_mode & stat.S_IRWXO:  # World readable
                return False, "Key file is world-readable (security risk)"
            
            # Try to read the file to check format
            with open(key_path, 'r') as f:
                content = f.read()
                
            # Check for common SSH key formats
            if "BEGIN" in content and "PRIVATE KEY" in content:
                return True, "Valid SSH key format"
            elif "-----BEGIN" in content:
                return True, "Valid SSH key format"
            else:
                return False, "Invalid SSH key format"
                
        except Exception as e:
            return False, f"Error reading key file: {e}"
    
    def get_supported_key_types(self):
        """Get list of supported SSH key types."""
        return ["RSA", "Ed25519", "ECDSA", "DSS"]
    
    def convert_putty_key(self, ppk_path, output_path):
        """
        Convert PuTTY .ppk key to OpenSSH format.
        This is a placeholder - actual conversion would require puttygen or similar.
        """
        self.log_message(">>> PuTTY .ppk conversion not implemented <<<", "WARNING")
        self.log_message(">>> Please use PuTTYgen to convert .ppk to OpenSSH format <<<", "INFO")
        self.log_message(">>> Or use ssh-keygen: ssh-keygen -i -f key.ppk > key.pem <<<", "INFO")
        return False
