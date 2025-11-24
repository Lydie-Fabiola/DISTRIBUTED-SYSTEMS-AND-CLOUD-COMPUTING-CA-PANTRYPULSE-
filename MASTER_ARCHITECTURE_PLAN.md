# 🏗️ MASTER ARCHITECTURE PLAN
## Production-Grade Distributed Cloud Storage System

**Vision:** Build a REAL distributed storage system like Google Drive/Amazon S3  
**Language:** Python (for rapid development and clarity)  
**Approach:** Everything from scratch - no frameworks, full control  
**Goal:** Real files, real IPs, real storage, real distributed system

---

## 🎯 CORE PRINCIPLES

### 1. **REAL, NOT SIMULATED**
- ✅ Files physically stored on disk
- ✅ Nodes have real IP addresses from network card
- ✅ Actual network communication (TCP/IP)
- ✅ Real file I/O operations
- ✅ Physical disk space consumption

### 2. **FULLY DISTRIBUTED**
- ✅ Each node operates independently
- ✅ No single point of failure (eventually)
- ✅ Nodes can join/leave dynamically
- ✅ Data replicated across multiple nodes
- ✅ Automatic failover and recovery

### 3. **PRODUCTION-GRADE**
- ✅ Persistent storage (SQLite databases)
- ✅ Comprehensive logging
- ✅ Error handling and recovery
- ✅ Security (authentication, encryption)
- ✅ Monitoring and metrics
- ✅ Scalable architecture

---

## 🏛️ SYSTEM ARCHITECTURE

### **Layer 1: Network Layer**
```
┌─────────────────────────────────────────────────────────┐
│  NETWORK CONTROLLER (Master Coordinator)                │
│  - Binds to real IP: 0.0.0.0:5000                      │
│  - Accepts connections from storage nodes               │
│  - Maintains node registry                              │
│  - Coordinates file operations                          │
│  - Manages metadata database                            │
└─────────────────────────────────────────────────────────┘
```

### **Layer 2: Storage Layer**
```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ STORAGE NODE │  │ STORAGE NODE │  │ STORAGE NODE │
│      1       │  │      2       │  │      3       │
│              │  │              │  │              │
│ IP: Dynamic  │  │ IP: Dynamic  │  │ IP: Dynamic  │
│ Port: 6001   │  │ Port: 6002   │  │ Port: 6003   │
│              │  │              │  │              │
│ Physical Dir:│  │ Physical Dir:│  │ Physical Dir:│
│ nodes/node1/ │  │ nodes/node2/ │  │ nodes/node3/ │
└──────────────┘  └──────────────┘  └──────────────┘
```

### **Layer 3: Data Layer**
```
Each node stores:
├─ chunks/           (Actual file chunks)
│  ├─ abc123.dat
│  ├─ def456.dat
│  └─ ...
├─ metadata.db       (SQLite database)
├─ node.log          (Operation logs)
└─ config.json       (Node configuration)
```

---

## 📊 DETAILED COMPONENT BREAKDOWN

### **COMPONENT 1: Network Controller**

**Purpose:** Master coordinator that manages the entire distributed system

**Responsibilities:**
1. **Node Management**
   - Register new nodes when they join
   - Track node health via heartbeats
   - Detect and handle node failures
   - Maintain up-to-date node registry

2. **Metadata Management**
   - Store file metadata (name, size, owner, chunks)
   - Track chunk locations across nodes
   - Manage replication information
   - Handle file versioning

3. **Request Coordination**
   - Route upload requests to appropriate nodes
   - Coordinate multi-node downloads
   - Balance load across nodes
   - Handle concurrent requests

4. **Fault Tolerance**
   - Detect node failures
   - Trigger re-replication of lost data
   - Maintain system consistency
   - Log all operations

**Data Structures:**
```python
# In-memory (fast access)
nodes = {
    'node1': {
        'ip': '192.168.1.101',
        'port': 6001,
        'status': 'ALIVE',
        'last_heartbeat': timestamp,
        'capacity': {'cpu': 4, 'memory': 8GB, 'storage': 100GB},
        'used': {'storage': 45GB, 'bandwidth': 500Mbps}
    }
}

# Persistent (SQLite database)
CREATE TABLE nodes (
    node_id TEXT PRIMARY KEY,
    ip_address TEXT,
    port INTEGER,
    status TEXT,
    capacity_json TEXT,
    registered_at TIMESTAMP
);

CREATE TABLE files (
    file_id TEXT PRIMARY KEY,
    filename TEXT,
    file_size INTEGER,
    owner TEXT,
    upload_date TIMESTAMP,
    chunk_count INTEGER,
    replication_factor INTEGER
);

CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    file_id TEXT,
    chunk_index INTEGER,
    chunk_size INTEGER,
    checksum TEXT,
    FOREIGN KEY (file_id) REFERENCES files(file_id)
);

CREATE TABLE chunk_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id TEXT,
    node_id TEXT,
    is_primary BOOLEAN,
    created_at TIMESTAMP,
    FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id),
    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);
```

**Network Protocol:**
```python
# Message format (JSON over TCP)
{
    "type": "REGISTER_NODE",
    "node_id": "node1",
    "ip": "192.168.1.101",
    "port": 6001,
    "capacity": {
        "cpu_cores": 4,
        "memory_gb": 8,
        "storage_gb": 100,
        "bandwidth_mbps": 1000
    }
}

{
    "type": "HEARTBEAT",
    "node_id": "node1",
    "timestamp": 1732185600.0,
    "metrics": {
        "cpu_usage": 45.2,
        "memory_usage": 60.5,
        "storage_used": 45.0,
        "active_transfers": 3
    }
}

{
    "type": "UPLOAD_REQUEST",
    "filename": "vacation.mp4",
    "file_size": 524288000,  # 500MB in bytes
    "checksum": "sha256_hash_here",
    "replication_factor": 3
}
```

---

### **COMPONENT 2: Storage Node**

**Purpose:** Independent storage unit that stores file chunks and serves requests

**Responsibilities:**
1. **Storage Management**
   - Store file chunks on physical disk
   - Track local storage usage
   - Manage disk space allocation
   - Clean up deleted chunks

2. **Network Communication**
   - Connect to network controller
   - Send periodic heartbeats
   - Receive and process requests
   - Transfer chunks to other nodes

3. **File Operations**
   - Receive and store chunks
   - Serve chunks for downloads
   - Verify chunk integrity (checksums)
   - Handle concurrent operations

4. **Health Monitoring**
   - Monitor resource usage
   - Report metrics to controller
   - Detect local failures
   - Graceful shutdown

**Physical Directory Structure:**
```
nodes/
└── node1/
    ├── chunks/                    # Actual file chunks
    │   ├── abc123def456.dat       # Chunk file
    │   ├── ghi789jkl012.dat
    │   └── ...
    ├── temp/                      # Temporary uploads
    │   └── upload_xyz.tmp
    ├── metadata.db                # Local SQLite database
    ├── node.log                   # Operation logs
    ├── config.json                # Node configuration
    └── stats.json                 # Runtime statistics
```

**Local Database Schema:**
```sql
CREATE TABLE local_chunks (
    chunk_id TEXT PRIMARY KEY,
    file_id TEXT,
    chunk_index INTEGER,
    file_path TEXT,              # Path to .dat file
    chunk_size INTEGER,
    checksum TEXT,
    stored_at TIMESTAMP,
    last_accessed TIMESTAMP
);

CREATE TABLE transfer_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT,              # UPLOAD, DOWNLOAD, DELETE
    chunk_id TEXT,
    remote_node TEXT,
    bytes_transferred INTEGER,
    duration_seconds REAL,
    timestamp TIMESTAMP
);
```

---

## 🔄 CORE WORKFLOWS

### **Workflow 1: Node Startup**
```
1. Node reads config.json
2. Creates physical directory structure
3. Initializes SQLite database
4. Binds to network port (e.g., 6001)
5. Connects to network controller
6. Sends REGISTER_NODE message
7. Waits for acknowledgment
8. Starts heartbeat thread
9. Starts request listener thread
10. Node is now ACTIVE
```

### **Workflow 2: File Upload (Complete Process)**
```
CLIENT SIDE:
1. User selects file: "vacation.mp4" (500MB)
2. Calculate SHA256 checksum
3. Send UPLOAD_REQUEST to controller

CONTROLLER SIDE:
4. Receive upload request
5. Generate unique file_id
6. Calculate chunk count (500MB / 10MB = 50 chunks)
7. Select target nodes based on:
   - Available storage space
   - Current load
   - Network proximity
8. Create metadata entries in database
9. Return upload plan to client

CLIENT SIDE:
10. Split file into 50 chunks (10MB each)
11. For each chunk:
    - Calculate chunk checksum
    - Send to assigned node(s)
    - Wait for confirmation
12. Update progress bar

NODE SIDE (for each chunk):
13. Receive chunk data
14. Verify checksum
15. Write to disk: chunks/abc123.dat
16. Update local database
17. Send confirmation to client
18. Notify controller of successful storage

CONTROLLER SIDE:
19. Update chunk_locations table
20. Trigger replication if needed
21. Mark file as COMPLETE
```

### **Workflow 3: File Download**
```
1. Client requests file: "vacation.mp4"
2. Controller looks up file metadata
3. Controller finds chunk locations
4. Controller returns chunk map to client
5. Client downloads chunks in parallel from multiple nodes
6. Client reassembles chunks into original file
7. Client verifies final checksum
8. Download complete
```

---

## 🔐 SECURITY CONSIDERATIONS

### **Authentication**
```python
# Token-based authentication
{
    "type": "REGISTER_NODE",
    "node_id": "node1",
    "auth_token": "sha256_hash_of_secret_key"
}
```

### **Encryption**
```python
# Encrypt chunks before storage
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

# Encrypt chunk
encrypted_chunk = cipher.encrypt(chunk_data)

# Decrypt chunk
decrypted_chunk = cipher.decrypt(encrypted_chunk)
```

---

**[CONTINUED IN NEXT FILE...]**

