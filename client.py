import socket
import threading
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# --- CONFIGURATION ---
SERVER_IP = "20.64.230.82"  # <--- YOUR AZURE IP
PORT = 5001
# ---------------------

class FileClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Group File Sharing App")
        self.root.geometry("500x450")
        
        self.client = None
        self.connected = False
        
        # Create Download Folder
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        # --- UI LAYOUT ---
        
        # Header / Status
        self.status_lbl = tk.Label(root, text="Status: Disconnected", fg="red", font=("Arial", 12, "bold"))
        self.status_lbl.pack(pady=10)

        # Login Frame (Password + Connect)
        login_frame = tk.Frame(root)
        login_frame.pack(pady=5)
        
        tk.Label(login_frame, text="Access Key:").grid(row=0, column=0, padx=5)
        
        self.pass_entry = tk.Entry(login_frame, show="*", width=20) # 'show=*' hides the password
        self.pass_entry.grid(row=0, column=1, padx=5)
        
        self.btn_connect = tk.Button(login_frame, text="Connect", command=self.connect_to_server, bg="#dddddd")
        self.btn_connect.grid(row=0, column=2, padx=5)

        # Action Buttons Frame
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=15)

        self.btn_list = tk.Button(btn_frame, text="List Files", command=self.list_files, state=tk.DISABLED, width=12)
        self.btn_list.grid(row=0, column=0, padx=5)

        self.btn_upload = tk.Button(btn_frame, text="Upload File", command=self.upload_file, state=tk.DISABLED, width=12)
        self.btn_upload.grid(row=0, column=1, padx=5)
        
        self.btn_download = tk.Button(btn_frame, text="Download File", command=self.ask_download, state=tk.DISABLED, width=12)
        self.btn_download.grid(row=0, column=2, padx=5)

        # Log Window
        self.log_area = scrolledtext.ScrolledText(root, width=55, height=15, state='disabled')
        self.log_area.pack(pady=10, padx=10)
        self.log("Welcome! Enter Access Key and click Connect.")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def connect_to_server(self):
        # GET PASSWORD FROM INPUT BOX
        password_input = self.pass_entry.get().strip()
        
        if not password_input:
            messagebox.showwarning("Input Error", "Please enter the Access Key!")
            return

        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.settimeout(5) # 5 second timeout
            self.client.connect((SERVER_IP, PORT))
            
            # Authentication
            msg = self.client.recv(1024).decode()
            if msg == "AUTH":
                # Send the typed password
                self.client.send(password_input.encode())
                
                response = self.client.recv(1024).decode()
                if response == "REJECT":
                    messagebox.showerror("Error", "Wrong Access Key! Connection Rejected.")
                    self.client.close()
                    return
            
            # If we get here, connection works
            self.client.settimeout(None) 
            self.connected = True
            
            # Update UI
            self.status_lbl.config(text="Status: Connected", fg="green")
            self.btn_connect.config(state=tk.DISABLED) # Disable connect button
            self.pass_entry.config(state=tk.DISABLED)  # Lock password box
            
            self.btn_list.config(state=tk.NORMAL)
            self.btn_upload.config(state=tk.NORMAL)
            self.btn_download.config(state=tk.NORMAL)
            self.log("SUCCESS: Connected to Azure Server!")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}\nCheck Azure Firewall or IP.")

    def list_files(self):
        if not self.connected: return
        try:
            self.client.send("LIST".encode())
            files = self.client.recv(4096).decode()
            self.log(f"Files on server:\n{files}")
        except:
            self.log("Error getting file list.")

    def upload_file(self):
        if not self.connected: return
        filepath = filedialog.askopenfilename()
        if not filepath: return

        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        
        self.log(f"Uploading {filename}...")
        threading.Thread(target=self._send_file_thread, args=(filename, filesize, filepath)).start()

    def _send_file_thread(self, filename, filesize, filepath):
        try:
            self.client.send(f"UPLOAD {filename} {filesize}".encode())
            self.client.recv(1024) 
            
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk: break
                    self.client.send(chunk)
            self.log(f"Upload of {filename} Complete.")
        except:
            self.log("Upload failed.")

    def ask_download(self):
        input_window = tk.Toplevel(self.root)
        input_window.title("Download")
        input_window.geometry("300x120")
        
        tk.Label(input_window, text="Enter filename exactly:").pack(pady=5)
        e = tk.Entry(input_window)
        e.pack(pady=5)
        
        def confirm():
            fname = e.get()
            input_window.destroy()
            self.download_file(fname)
            
        tk.Button(input_window, text="Download", command=confirm).pack(pady=10)

    def download_file(self, filename):
        if not self.connected: return
        self.log(f"Requesting {filename}...")
        threading.Thread(target=self._recv_file_thread, args=(filename,)).start()

    def _recv_file_thread(self, filename):
        try:
            self.client.send(f"DOWNLOAD {filename}".encode())
            response = self.client.recv(1024).decode().split()
            
            if response[0] == "EXISTS":
                filesize = int(response[1])
                save_path = os.path.join("downloads", filename)
                
                received = 0
                with open(save_path, "wb") as f:
                    while received < filesize:
                        chunk = self.client.recv(4096)
                        if not chunk: break
                        f.write(chunk)
                        received += len(chunk)
                self.log(f"Saved to {save_path}")
                messagebox.showinfo("Success", f"File saved in 'downloads' folder!")
            else:
                self.log("File does not exist on server.")
                messagebox.showerror("Error", "File not found on server.")
        except:
            self.log("Download failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileClientGUI(root)
    root.mainloop()