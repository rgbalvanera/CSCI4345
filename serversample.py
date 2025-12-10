import socket
import threading
import os

# CONFIGURATION
HOST = '0.0.0.0'
PORT = 5001
ACCESS_KEY = "SuperSecretKey123"
STORAGE_DIR = "shared_files"

# Create storage directory if it doesn't exist
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

def handle_client(conn, addr):
    print(f"[+] New connection from {addr}")
    
    try:
        # 1. AUTHENTICATION
        conn.send("AUTH".encode())
        password = conn.recv(1024).decode()
        
        if password != ACCESS_KEY:
            conn.send("REJECT".encode())
            print(f"[-] {addr} failed authentication.")
            conn.close()
            return
        
        conn.send("OK".encode())
        
        # 2. COMMAND LOOP
        while True:
            # Wait for command (e.g., "UPLOAD file.txt" or "LIST")
            request = conn.recv(1024).decode()
            if not request: break
            
            command, *args = request.split()
            
            if command == "UPLOAD":
                filename = args[0]
                file_size = int(args[1])
                conn.send("READY".encode())
                
                # Receive file data
                filepath = os.path.join(STORAGE_DIR, filename)
                received = 0
                with open(filepath, "wb") as f:
                    while received < file_size:
                        chunk = conn.recv(4096)
                        if not chunk: break
                        f.write(chunk)
                        received += len(chunk)
                print(f"[+] Received {filename} from {addr}")
                
            elif command == "LIST":
                # Send list of available files
                files = os.listdir(STORAGE_DIR)
                conn.send(str(files).encode())
                
            elif command == "DOWNLOAD":
                filename = args[0]
                filepath = os.path.join(STORAGE_DIR, filename)
                if os.path.exists(filepath):
                    filesize = os.path.getsize(filepath)
                    conn.send(f"EXISTS {filesize}".encode())
                    
                    # Send file data
                    with open(filepath, "rb") as f:
                        while True:
                            chunk = f.read(4096)
                            if not chunk: break
                            conn.send(chunk)
                else:
                    conn.send("ERROR".encode())

    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        conn.close()

# MAIN SERVER LOOP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()
print(f"[*] Group File Server Listening on {PORT}...")

while True:
    conn, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(conn, addr))
    thread.start()
