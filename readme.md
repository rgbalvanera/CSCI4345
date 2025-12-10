# ☁️ Multi-Tenant Cloud File Sharing System

**Course:** CSCI 4345 - Computer Networks  
**Team Members:** Ricardo Balvanera, Armando Gonzalez  
**Platform:** Python (Tkinter) + Microsoft Azure  

## 📖 Project Overview
This project is a custom-built **Client-Server File Sharing Application** that allows users to create private groups, upload files, and download them from a central cloud server.

The system is deployed on a **Microsoft Azure Virtual Machine (Ubuntu)**, acting as a central hub. Clients connect via a Graphical User Interface (GUI) running on their local laptops, utilizing **TCP Sockets** for reliable data transmission.

## 🚀 Key Features
*   **Multi-Group Support:** Users can create distinct groups (e.g., "FamilyTrip", "Work"). Files are isolated—Group A cannot see Group B's files.
*   **Secure Authentication:** Requires Group Name and Password to access storage.
*   **GUI Client:** Built with `tkinter`, featuring a searchable download list and status logs.
*   **Concurrent Connections:** The server uses **Multi-threading** to handle multiple users uploading/downloading simultaneously.
*   **Robust File Transfer:**
    *   Auto-renaming (converts spaces to underscores).
    *   Chunked data transfer (handles large files without crashing RAM).
    *   Synchronization logic (prevents data collision).

## 🛠️ Technologies & Protocols
*   **Language:** Python 3.10+
*   **Transport Layer:** TCP (Transmission Control Protocol) via `socket` library.
*   **Cloud Infrastructure:** Microsoft Azure VM (Standard_B1s, Ubuntu 24.04).
*   **Port:** 5001 (Custom configured via Azure Network Security Group).
*   **Serialization:** JSON (for storing group credentials).

---

## ⚙️ Installation & Setup

### 1. Server-Side (Azure VM)
The server runs on an Ubuntu Virtual Machine.

```bash
# 1. Update system
sudo apt update

# 2. Upload the server.py file to the VM (via SCP or Copy/Paste)

# 3. Run the Server
python3 server.py
```
*Note: Ensure Port 5001 is open in the Azure "Networking" tab (Inbound Rule).*

### 2. Client-Side (Local Laptop)
The client runs on Windows/Mac/Linux.

```bash
# 1. Ensure Python is installed
python --version

# 2. Open client.py and verify the SERVER_IP matches your Azure VM IP
# SERVER_IP = "20.64.230.82"

# 3. Run the Client
python client.py
```

---

## 🕹️ How to Use

1.  **Start the Server** on Azure.
2.  **Launch the Client** on your laptop.
3.  **Create a Group:**
    *   Enter a new Group Name (e.g., `FinalProject`) and Password.
    *   Click **"Create New Group"**.
4.  **Login:**
    *   Enter the credentials you just created.
    *   Click **"Login"**.
5.  **Upload:**
    *   Click **"Upload File"** and select a file from your computer.
    *   *Note: Spaces in filenames are automatically converted to `_`.*
6.  **Download:**
    *   Click **"Download File"**.
    *   A search window will appear. Type to filter files.
    *   Select a file and click **Download**. The file will appear in a `downloads/` folder.

---

## 🐛 Troubleshooting / Common Issues

**"Address already in use" on Server:**
If the server crashed but the port is still locked:
```bash
sudo fuser -k 5001/tcp
python3 server.py
```

**"Connection Timeout" on Client:**
*   Check if the Azure VM is running.
*   Check if the Azure Firewall (NSG) has **Port 5001 (TCP)** allowed.

**"Download Failed":**
*   Ensure both Client and Server code have the `time.sleep(0.1)` synchronization fix included to prevent header/body data collision.

---

## 📂 Project Structure

```text
/NetworkProject
│
├── server.py           # Runs on Azure. Handles storage, auth, and routing.
├── client.py           # GUI Application for users, ran locally
├── groups.json         # Database of Group Names & Passwords (Auto-generated).
└── downloads/          # Local folder where client saves downloaded files.
```

---

## 🎓 Academic Concepts Demonstrated
This project demonstrates mastery of:
1.  **Socket Programming:** Manually managing byte streams (`recv`, `send`).
2.  **Application Layer Protocols:** Designed a custom protocol for `UPLOAD`, `DOWNLOAD`, `LIST`, and `AUTH`.
3.  **Race Conditions:** Solved networking timing issues using acknowledgments and buffer delays.
4.  **Cloud Deployment:** Real-world implementation of IaaS.

