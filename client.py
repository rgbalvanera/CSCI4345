import socket
import time
import threading
import os
import ast
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# --- CONFIGURATION ---
SERVER_IP = "20.64.230.82"  # <--- YOUR AZURE IP
PORT = 5001
# ---------------------

class FileClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-Group File Cloud")
        self.root.geometry("500x550")
        
        self.client = None
        self.connected = False
        
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        # UI SETUP
        self.status_lbl = tk.Label(root, text="Status: Disconnected", fg="red", font=("Arial", 12, "bold"))
        self.status_lbl.pack(pady=10)

        login_frame = tk.Frame(root, borderwidth=2, relief="groove")
        login_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(login_frame, text="Group Name:").grid(row=0, column=0, padx=5, pady=5)
        self.group_entry = tk.Entry(login_frame, width=20)
        self.group_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        self.pass_entry = tk.Entry(login_frame, show="*", width=20)
        self.pass_entry.grid(row=1, column=1, padx=5, pady=5)
        
        self.btn_connect = tk.Button(login_frame, text="Login", command=self.login_to_server, bg="#cce5ff", width=15)
        self.btn_connect.grid(row=2, column=0, columnspan=2, pady=5)

        self.btn_register = tk.Button(login_frame, text="Create New Group", command=self.register_group, bg="#e6ffcc", width=15)
        self.btn_register.grid(row=3, column=0, columnspan=2, pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=15)

        self.btn_list = tk.Button(btn_frame, text="List Files", command=self.list_files, state=tk.DISABLED, width=12)
        self.btn_list.grid(row=0, column=0, padx=5)

        self.btn_upload = tk.Button(btn_frame, text="Upload File", command=self.upload_file, state=tk.DISABLED, width=12)
        self.btn_upload.grid(row=0, column=1, padx=5)
        
        self.btn_download = tk.Button(btn_frame, text="Download File", command=self.ask_download, state=tk.DISABLED, width=12)
        self.btn_download.grid(row=0, column=2, padx=5)

        self.log_area = scrolledtext.ScrolledText(root, width=55, height=15, state='disabled')
        self.log_area.pack(pady=10, padx=10)
        self.log("Welcome! Login or Create a New Group.")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def _connect_socket(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((SERVER_IP, PORT))
            return s
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot reach server: {e}")
            return None

    def register_group(self):
        group = self.group_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not group or not password:
            messagebox.showwarning("Input Error", "Enter Group Name and Password.")
            return

        sock = self._connect_socket()
        if not sock: return
        try:
            if sock.recv(1024).decode() == "AUTH":
                sock.send(f"REGISTER:{group}:{password}".encode())
                resp = sock.recv(1024).decode()
                if resp == "CREATED":
                    messagebox.showinfo("Success", f"Group '{group}' created!")
                elif resp == "EXISTS":
                    messagebox.showerror("Error", "Group Name taken.")
            sock.close()
        except: pass

    def login_to_server(self):
        group = self.group_entry.get().strip()
        password = self.pass_entry.get().strip()
        if not group or not password:
            messagebox.showwarning("Input Error", "Enter Group Name and Password.")
            return

        self.client = self._connect_socket()
        if not self.client: return

        try:
            if self.client.recv(1024).decode() == "AUTH":
                self.client.send(f"LOGIN:{group}:{password}".encode())
                if self.client.recv(1024).decode() == "REJECT":
                    messagebox.showerror("Error", "Login Failed.")
                    self.client.close()
                    return
            
            self.client.settimeout(None)
            self.connected = True
            
            self.status_lbl.config(text=f"Connected to: {group}", fg="green")
            self.btn_connect.config(state=tk.DISABLED)
            self.btn_register.config(state=tk.DISABLED)
            self.group_entry.config(state=tk.DISABLED)
            self.pass_entry.config(state=tk.DISABLED)
            self.btn_list.config(state=tk.NORMAL)
            self.btn_upload.config(state=tk.NORMAL)
            self.btn_download.config(state=tk.NORMAL)
            self.log(f"SUCCESS: Logged into '{group}'.")
        except: pass

    def list_files(self):
        if not self.connected: return
        try:
            self.client.send("LIST".encode())
            files = self.client.recv(4096).decode()
            self.log(f"Files:\n{files}")
            return files
        except: return "[]"

    def upload_file(self):
        if not self.connected: return
        filepath = filedialog.askopenfilename()
        if not filepath: return

        filename = os.path.basename(filepath)
        # --- AUTO-RENAME FIX ---
        # Replace spaces with underscores automatically
        filename = filename.replace(" ", "_")
        # -----------------------
        
        filesize = os.path.getsize(filepath)
        self.log(f"Uploading {filename}...")
        threading.Thread(target=self._send_file_thread, args=(filename, filesize, filepath)).start()

    def _send_file_thread(self, filename, filesize, filepath):
        self.btn_upload.config(state=tk.DISABLED)
        try:
            # Simple space separator now that filenames are safe
            self.client.send(f"UPLOAD {filename} {filesize}".encode())
            self.client.recv(1024) 
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk: break
                    self.client.send(chunk)
            
            self.client.recv(1024) # Wait for UPLOAD_COMPLETE
            self.log("Upload Complete.")
            messagebox.showinfo("Success", f"Uploaded as {filename}")
        except:
            self.log("Upload failed.")
        self.btn_upload.config(state=tk.NORMAL)

    def ask_download(self):
        try:
            self.client.send("LIST".encode())
            response = self.client.recv(4096).decode()
            all_files = ast.literal_eval(response)
        except:
            messagebox.showerror("Error", "Could not fetch list.")
            return

        if not all_files:
            messagebox.showinfo("Info", "No files found.")
            return

        win = tk.Toplevel(self.root)
        win.title("Download Manager")
        win.geometry("300x400")
        
        tk.Label(win, text="Search Files:", font=("Arial", 10, "bold")).pack(pady=5)
        search_var = tk.StringVar()
        entry = tk.Entry(win, textvariable=search_var)
        entry.pack(fill="x", padx=10)
        
        frame = tk.Frame(win)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, height=15)
        listbox.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        def update_list(*args):
            term = search_var.get().lower()
            listbox.delete(0, tk.END)
            for item in all_files:
                if term in item.lower():
                    listbox.insert(tk.END, item)
        search_var.trace("w", update_list)
        update_list()

        def do_download():
            sel = listbox.curselection()
            if not sel: return
            fname = listbox.get(sel[0])
            win.destroy()
            self.download_file(fname)
            
        tk.Button(win, text="Download", command=do_download, bg="#ccffcc").pack(pady=10)

    def download_file(self, filename):
        if not self.connected: return
        self.log(f"Requesting {filename}...")
        threading.Thread(target=self._recv_file_thread, args=(filename,)).start()

    def _recv_file_thread(self, filename):
        try:
            self.client.send(f"DOWNLOAD {filename}".encode())
            
            # 1. Get the Header
            response = self.client.recv(1024).decode().split()
            
            if len(response) >= 2 and response[0] == "EXISTS":
                filesize = int(response[1])
                
                # --- FIX: Wait 0.1s to ensure the buffer is clear ---
                time.sleep(0.1) 
                # ----------------------------------------------------

                save_path = os.path.join("downloads", filename)
                received = 0
                
                # 2. Get the Body
                with open(save_path, "wb") as f:
                    while received < filesize:
                        chunk = self.client.recv(4096)
                        if not chunk: break
                        f.write(chunk)
                        received += len(chunk)
                
                self.log(f"Saved to {save_path}")
                messagebox.showinfo("Success", f"Downloaded: {filename}")
            else:
                self.log("File not found.")
                messagebox.showerror("Error", "File not found on server.")
        except Exception as e:
            self.log(f"Download failed: {e}")
    
if __name__ == "__main__":
    root = tk.Tk()
    app = FileClientGUI(root)
    root.mainloop()