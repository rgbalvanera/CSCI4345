#this file should never be executed directly
#it exists solely to see what code is on the server side in our azure vm
# to run the server code perform the following command in terminal:
# ssh -i path/tofile/NetworksFinal_key.pem <your-username>@<your-vm-ip-address>
# for <your-username>@<your-vm-ip-address> it can be replaced with azureazureuser@20.64.230.82
# next run:
# python3 server.py
# after running the server code you can then run the client code on your local machine

import socket
import threading
import os
import json
import time

# --- CONFIGURATION ---
HOST = '0.0.0.0'
PORT = 5001
BASE_STORAGE_DIR = "shared_files"
DB_FILE = "groups.json"

# --- DATABASE HELPERS ---
def load_groups():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_groups(groups_dict):
    with open(DB_FILE, "w") as f:
        json.dump(groups_dict, f)

GROUPS = load_groups()

if not os.path.exists(BASE_STORAGE_DIR):
    os.makedirs(BASE_STORAGE_DIR)

def handle_client(conn, addr):
    print(f"[+] Connection attempt from {addr}")
    current_group_path = None
    
    try:
        conn.send("AUTH".encode())
        request_data = conn.recv(1024).decode().strip()
        
        try:
            tag, group_name, password = request_data.split(":")
        except ValueError:
            conn.send("INVALID_FORMAT".encode())
            conn.close()
            return

        # REGISTER
        if tag == "REGISTER":
            if group_name in GROUPS:
                conn.send("EXISTS".encode()) 
            else:
                GROUPS[group_name] = password
                save_groups(GROUPS) 
                group_path = os.path.join(BASE_STORAGE_DIR, group_name)
                if not os.path.exists(group_path):
                    os.makedirs(group_path)
                conn.send("CREATED".encode())
                print(f"[+] Created group: {group_name}")
            conn.close()
            return

        # LOGIN
        elif tag == "LOGIN":
            if group_name in GROUPS and GROUPS[group_name] == password:
                conn.send("OK".encode())
                print(f"[+] {addr} logged into: {group_name}")
                current_group_path = os.path.join(BASE_STORAGE_DIR, group_name)
                if not os.path.exists(current_group_path):
                    os.makedirs(current_group_path)
            else:
                conn.send("REJECT".encode())
                conn.close()
                return

        # COMMAND LOOP
        while True:
            request = conn.recv(1024).decode()
            if not request: break
            
            parts = request.split()
            if not parts: continue
            
            command = parts[0]
            
            if command == "UPLOAD":
                filename = parts[1]
                file_size = int(parts[2])
                conn.send("READY".encode())
                
                filepath = os.path.join(current_group_path, filename)
                received = 0
                with open(filepath, "wb") as f:
                    while received < file_size:
                        chunk = conn.recv(4096)
                        if not chunk: break
                        f.write(chunk)
                        received += len(chunk)
                
                conn.send("UPLOAD_COMPLETE".encode())
                print(f"[+] Uploaded: {filename}")
                
            elif command == "LIST":
                files = os.listdir(current_group_path)
                conn.send(str(files).encode())
                
            elif command == "DOWNLOAD":
                filename = parts[1]
                filepath = os.path.join(current_group_path, filename)
                
                print(f"DEBUG: Client requested '{filename}'")
                print(f"DEBUG: Looking in path -> {filepath}")
                
                if os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)
                    print(f"DEBUG: File found! Size: {filesize}")
                    conn.send(f"EXISTS {filesize}".encode())
                    
                    
                    time.sleep(0.1) 

                    
                    with open(filepath, "rb") as f:
                        while True:
                            chunk = f.read(4096)
                            if not chunk: break
                            conn.send(chunk)
                else:
                    print(f"DEBUG: ERROR - FILE NOT FOUND")
                    conn.send("ERROR".encode())

    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        conn.close()

# MAIN SERVER STARTUP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
server.bind((HOST, PORT))
server.listen()
print(f"[*] Server Listening on {PORT}...")

while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()
