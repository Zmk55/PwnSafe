import customtkinter as ctk
from tkinter import filedialog
import paramiko
import threading


class BackupRestoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Backup & Restore Utility")
        self.geometry("600x400")
        ctk.set_appearance_mode("System")  # Options: "Light", "Dark", "System"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        # Header
        self.header_label = ctk.CTkLabel(self, text="Backup & Restore Utility", font=("Arial", 20, "bold"))
        self.header_label.pack(pady=10)

        # Host, Username, Password Section
        self.frame = ctk.CTkFrame(self, corner_radius=10)
        self.frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.frame, text="Remote Host (IP/Hostname):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.host_entry = ctk.CTkEntry(self.frame, placeholder_text="e.g., 10.0.0.2", width=200)
        self.host_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(self.frame, text="Username:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.user_entry = ctk.CTkEntry(self.frame, placeholder_text="e.g., pi", width=200)
        self.user_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(self.frame, text="Password:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.pass_entry = ctk.CTkEntry(self.frame, placeholder_text="Enter your password", show="*", width=200)
        self.pass_entry.grid(row=2, column=1, padx=10, pady=5)

        # Backup File Section
        ctk.CTkLabel(self.frame, text="Backup File:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.file_entry = ctk.CTkEntry(self.frame, placeholder_text="Select backup file...", width=200)
        self.file_entry.grid(row=3, column=1, padx=10, pady=5)

        self.browse_button = ctk.CTkButton(self.frame, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=3, column=2, padx=10, pady=5)

        # Buttons for Backup & Restore
        self.backup_button = ctk.CTkButton(self, text="Backup", command=self.start_backup, width=120)
        self.backup_button.pack(side="left", padx=20, pady=10)

        self.restore_button = ctk.CTkButton(self, text="Restore", command=self.start_restore, width=120)
        self.restore_button.pack(side="left", padx=20, pady=10)

        # Output Log
        self.output_text = ctk.CTkTextbox(self, width=500, height=200, corner_radius=10)
        self.output_text.pack(pady=10, padx=20, fill="x")

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Backup Files", "*.tgz")])
        if filename:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, filename)

    def log_message(self, message, color="white"):
        self.output_text.insert("end", f"{message}\n")
        self.output_text.see("end")

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
            self.log_message(f"[ERROR] SSH Connection Failed: {e}", "red")
            return None

    def start_backup(self):
        threading.Thread(target=self.backup, daemon=True).start()

    def backup(self):
        ssh = self.ssh_connect()
        if ssh:
            self.log_message("[INFO] Starting backup...")
            command = "sudo tar -czf /tmp/backup.tgz /etc/pwnagotchi/ /root/.ssh /home/pi/handshakes"
            stdin, stdout, stderr = ssh.exec_command(command)
            errors = stderr.read().decode()
            if errors:
                self.log_message(f"[ERROR] {errors}", "red")
            else:
                self.log_message("[INFO] Backup completed successfully!")
            ssh.close()

    def start_restore(self):
        threading.Thread(target=self.restore, daemon=True).start()

    def restore(self):
        ssh = self.ssh_connect()
        if ssh:
            backup_file = self.file_entry.get()
            if not backup_file:
                self.log_message("[ERROR] No backup file selected!", "red")
                return

            self.log_message(f"[INFO] Uploading {backup_file}...")
            try:
                sftp = ssh.open_sftp()
                sftp.put(backup_file, "/tmp/restore.tgz")
                sftp.close()
                self.log_message("[INFO] File uploaded successfully.")
            except Exception as e:
                self.log_message(f"[ERROR] Failed to upload file: {e}", "red")
                return

            self.log_message("[INFO] Restoring backup on remote device...")
            command = "sudo tar -xzvf /tmp/restore.tgz -C /"
            stdin, stdout, stderr = ssh.exec_command(command)
            errors = stderr.read().decode()
            if errors:
                self.log_message(f"[ERROR] {errors}", "red")
            else:
                self.log_message("[INFO] Restore completed successfully!")
            ssh.close()


if __name__ == "__main__":
    app = BackupRestoreApp()
    app.mainloop()
