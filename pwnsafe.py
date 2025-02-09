import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import paramiko
import threading

class BackupRestoreApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Backup & Restore Utility")
        
        # Labels and Entry Fields
        tk.Label(root, text="Remote Host (IP/Hostname):").grid(row=0, column=0, sticky="w")
        self.host_entry = tk.Entry(root, width=30)
        self.host_entry.grid(row=0, column=1)
        self.host_entry.insert(0, "10.0.0.2")
        
        tk.Label(root, text="Username:").grid(row=1, column=0, sticky="w")
        self.user_entry = tk.Entry(root, width=30)
        self.user_entry.grid(row=1, column=1)
        self.user_entry.insert(0, "pi")
        
        tk.Label(root, text="Password:").grid(row=2, column=0, sticky="w")
        self.pass_entry = tk.Entry(root, width=30, show="*")
        self.pass_entry.grid(row=2, column=1)
        
        tk.Label(root, text="Backup File:").grid(row=3, column=0, sticky="w")
        self.file_entry = tk.Entry(root, width=30)
        self.file_entry.grid(row=3, column=1)
        
        tk.Button(root, text="Browse", command=self.browse_file).grid(row=3, column=2)
        
        # Buttons for Actions
        tk.Button(root, text="Backup", command=self.start_backup).grid(row=4, column=0, pady=10)
        tk.Button(root, text="Restore", command=self.start_restore).grid(row=4, column=1, pady=10)
        
        # Output Console
        self.output = scrolledtext.ScrolledText(root, width=60, height=15, wrap=tk.WORD)
        self.output.grid(row=5, column=0, columnspan=3)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Backup Files", "*.tgz")])
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
    
    def log_message(self, message):
        self.output.insert(tk.END, message + "\n")
        self.output.see(tk.END)
    
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
            self.log_message(f"[ERROR] SSH Connection Failed: {e}")
            return None
    
    def start_backup(self):
        threading.Thread(target=self.backup, daemon=True).start()
    
    def backup(self):
        ssh = self.ssh_connect()
        if ssh:
            self.log_message("[INFO] Starting backup...")
            command = "sudo tar -czf /tmp/backup.tgz /etc/pwnagotchi/ /root/.ssh /home/pi/handshakes"
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            errors = stderr.read().decode()
            if errors:
                self.log_message(f"[ERROR] {errors}")
            else:
                self.log_message("[INFO] Backup completed: /tmp/backup.tgz")
            ssh.close()
    
    def start_restore(self):
        threading.Thread(target=self.restore, daemon=True).start()
    
    def restore(self):
        ssh = self.ssh_connect()
        if ssh:
            backup_file = self.file_entry.get()
            if not backup_file:
                self.log_message("[ERROR] No backup file selected!")
                return
            
            self.log_message(f"[INFO] Uploading {backup_file} to remote device...")
            
            try:
                sftp = ssh.open_sftp()
                sftp.put(backup_file, "/tmp/restore.tgz")
                sftp.close()
                self.log_message("[INFO] File uploaded successfully.")
            except Exception as e:
                self.log_message(f"[ERROR] Failed to upload file: {e}")
                return
            
            self.log_message("[INFO] Extracting backup on remote device...")
            command = "sudo tar -xzvf /tmp/restore.tgz -C /"
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode()
            errors = stderr.read().decode()
            
            if errors:
                self.log_message(f"[ERROR] {errors}")
            else:
                self.log_message("[INFO] Restore completed successfully!")
            ssh.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = BackupRestoreApp(root)
    root.mainloop()
