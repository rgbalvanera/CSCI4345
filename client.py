import socket
import os

SERVER_IP = "YOUR_AZURE_VM_IP" # <--- Update this!
PORT = 5001
ACCESS_KEY = "SuperSecretKey123"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))

# 1. AUTHENTICATION
msg = client.recv(1024).decode()
if msg == "AUTH":
    client.send(ACCESS_KEY.encode())
    response = client.recv(1024).decode()
    if response == "REJECT":
        print("Wrong password!")
        exit()
    print("Connected to Group Server!")

while True:
    action = input("Enter command (upload <file> | download <file> | list): ").strip().split()
    cmd = action[0].upper()

    if cmd == "UPLOAD":
        filename = action[1]
        if os.path.exists(filename):
            filesize = os.path.getsize(filename)
            client.send(f"UPLOAD {filename} {filesize}".encode())
            
            # Wait for server ready
            client.recv(1024) 
            
            with open(filename, "rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk: break
                    client.send(chunk)
            print("Upload Complete.")
        else:
            print("File not found!")

    elif cmd == "LIST":
        client.send("LIST".encode())
        print("Files on server:", client.recv(4096).decode())

    elif cmd == "DOWNLOAD":
        filename = action[1]
        client.send(f"DOWNLOAD {filename}".encode())
        response = client.recv(1024).decode().split()
        
        if response[0] == "EXISTS":
            filesize = int(response[1])
            received = 0
            with open(f"downloaded_{filename}", "wb") as f:
                while received < filesize:
                    chunk = client.recv(4096)
                    f.write(chunk)
                    received += len(chunk)
            print("Download Complete.")
        else:
            print("File does not exist on server.")
