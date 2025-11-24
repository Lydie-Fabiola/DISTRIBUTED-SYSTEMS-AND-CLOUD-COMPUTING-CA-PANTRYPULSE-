# 🎯 PROJECT VISION AND COMPREHENSIVE PLAN
## Real Distributed Cloud Storage System - Like Google Drive/Amazon S3

**Date:** November 21, 2025  
**Project Owner:** KENFACK LYDIE FABIOLA  
**Vision:** Build a REAL, production-grade distributed storage system from scratch

---

## ✅ I UNDERSTAND YOUR VISION

You want to build a **REAL distributed cloud storage system** where:

1. ✅ **Real Files** - Files are actually stored on physical disk, not simulated
2. ✅ **Real IP Addresses** - Nodes have real IPs assigned by your network card
3. ✅ **Real Network Communication** - Actual TCP/IP sockets, not fake
4. ✅ **Independent Nodes** - Each node operates like a virtual machine
5. ✅ **Dynamic Scaling** - Create as many nodes as you want
6. ✅ **Physical Disk Space** - Nodes actually consume hard drive space
7. ✅ **Real File Operations** - Upload, download, delete, list - all real
8. ✅ **Like Google Drive** - Works exactly like real cloud storage

**NO SIMULATION. NO FAKE IMPLEMENTATION. EVERYTHING REAL.**

---

## 🏗️ HOW GOOGLE DRIVE ACTUALLY WORKS (Deep Analysis)

### **1. Client Application (Your Computer)**
When you drag a file into Google Drive:

```
Step 1: File Watcher detects new file
Step 2: Calculate SHA256 checksum
Step 3: Check if file already exists (deduplication)
Step 4: Split file into 8MB chunks
Step 5: Encrypt each chunk (AES-256)
Step 6: Upload chunks in parallel to nearest data center
Step 7: Verify each chunk with checksum
Step 8: Update metadata database
```

### **2. Load Balancer (Google's Frontend)**
```
Step 1: Receive your request
Step 2: Authenticate your token
Step 3: Find nearest data center (latency-based)
Step 4: Check data center load
Step 5: Route request to best server
```

### **3. Metadata Layer (Spanner/Bigtable)**
```
Stores:
- File metadata (name, size, owner, permissions)
- Chunk IDs and their locations
- Version history
- Sharing permissions
- Access logs
```

### **4. Storage Layer (Colossus)**
```
Physical Storage:
- Chunk files stored on disk
- Each chunk replicated 3x minimum
- Stored in different racks/data centers
- Erasure coding for efficiency
```

### **5. Replication Strategy**
```
Every chunk stored in:
- 3 different servers (hardware failure)
- 2 different racks (power failure)
- 2 different data centers (disaster recovery)

If server dies → automatic re-replication
```

---

## 🎯 OUR SYSTEM ARCHITECTURE (EXACTLY WHAT WE'LL BUILD)

### **System Overview**
```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR COMPUTER (Windows)                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  NETWORK CONTROLLER (Master Coordinator)                │   │
│  │  - Real IP: 0.0.0.0:5000 (binds to all interfaces)     │   │
│  │  - SQLite Database: controller_data/controller.db       │   │
│  │  - Manages all nodes and file metadata                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ STORAGE NODE │  │ STORAGE NODE │  │ STORAGE NODE │         │
│  │      1       │  │      2       │  │      3       │         │
│  │              │  │              │  │              │         │
│  │ Real IP:     │  │ Real IP:     │  │ Real IP:     │         │
│  │ 127.0.0.1    │  │ 127.0.0.1    │  │ 127.0.0.1    │         │
│  │ Port: 6001   │  │ Port: 6002   │  │ Port: 6003   │         │
│  │              │  │              │  │              │         │
│  │ Physical:    │  │ Physical:    │  │ Physical:    │         │
│  │ nodes/node1/ │  │ nodes/node2/ │  │ nodes/node3/ │         │
│  │  ├─chunks/   │  │  ├─chunks/   │  │  ├─chunks/   │         │
│  │  ├─metadata. │  │  ├─metadata. │  │  ├─metadata. │         │
│  │  │  db       │  │  │  db       │  │  │  db       │         │
│  │  └─node.log  │  │  └─node.log  │  │  └─node.log  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  All communicate via TCP/IP sockets with JSON messages         │
└─────────────────────────────────────────────────────────────────┘
```

### **Physical Directory Structure**
```
CloudSim/
├── controller_data/
│   ├── controller.db          # SQLite database
│   └── controller.log         # Controller logs
│
├── nodes/
│   ├── node1/
│   │   ├── chunks/            # Actual file chunks
│   │   │   ├── abc123.dat     # Real file on disk
│   │   │   ├── def456.dat
│   │   │   └── ...
│   │   ├── temp/              # Temporary uploads
│   │   ├── metadata.db        # Node's local database
│   │   ├── node.log           # Node operation logs
│   │   └── config.json        # Node configuration
│   │
│   ├── node2/
│   │   └── ... (same structure)
│   │
│   └── node3/
│       └── ... (same structure)
│
├── core/                      # Core system components
├── network/                   # Networking code
├── storage/                   # Storage management
└── utils/                     # Utilities
```

---

## 🔄 COMPLETE WORKFLOWS (EXACTLY HOW IT WORKS)

### **Workflow 1: Starting the System**

**Terminal 1 - Start Controller:**
```bash
python main_controller.py --host 0.0.0.0 --port 5000
```

**What happens:**
```
1. Controller binds to 0.0.0.0:5000 (real TCP socket)
2. Creates/opens SQLite database: controller_data/controller.db
3. Initializes tables: nodes, files, chunks, chunk_locations
4. Starts TCP server listening for connections
5. Starts heartbeat monitor thread
6. Prints: "Controller ready on 0.0.0.0:5000"
```

**Terminal 2 - Start Node 1:**
```bash
python main_node.py --node-id node1 --port 6001 --storage 50GB --controller localhost:5000
```

**What happens:**
```
1. Creates physical directory: nodes/node1/
2. Creates subdirectories: chunks/, temp/
3. Creates SQLite database: nodes/node1/metadata.db
4. Binds to TCP port 6001 (real socket)
5. Connects to controller at localhost:5000
6. Sends REGISTER_NODE message with:
   - node_id: "node1"
   - ip: "127.0.0.1"
   - port: 6001
   - capacity: {storage: 50GB, ...}
7. Receives REGISTER_ACK from controller
8. Starts heartbeat thread (sends heartbeat every 2 seconds)
9. Starts request listener thread
10. Prints: "Node node1 ready on 127.0.0.1:6001"
```

**Terminal 3 - Start Node 2:**
```bash
python main_node.py --node-id node2 --port 6002 --storage 100GB --controller localhost:5000
```

**Terminal 4 - Start Node 3:**
```bash
python main_node.py --node-id node3 --port 6003 --storage 75GB --controller localhost:5000
```

---

### **Workflow 2: Uploading a File (COMPLETE PROCESS)**

**User Command:**
```bash
python client.py upload vacation.mp4
```

**Step-by-Step Process:**

**CLIENT SIDE:**
```
1. Read file: vacation.mp4 (500MB)
2. Calculate SHA256 checksum: abc123def456...
3. Connect to controller at localhost:5000
4. Send UPLOAD_REQUEST:
   {
     "type": "UPLOAD_REQUEST",
     "payload": {
       "filename": "vacation.mp4",
       "file_size": 524288000,  # 500MB in bytes
       "checksum": "abc123def456...",
       "replication_factor": 3
     }
   }
```

**CONTROLLER SIDE:**
```
5. Receive UPLOAD_REQUEST
6. Generate unique file_id: "file_xyz789"
7. Calculate chunks: 500MB / 10MB = 50 chunks
8. Select nodes for each chunk:
   - Check available storage on each node
   - Balance load across nodes
   - Ensure replication factor of 3
   
9. Create chunk assignment plan:
   Chunk 0: primary=node1, replicas=[node2, node3]
   Chunk 1: primary=node2, replicas=[node1, node3]
   Chunk 2: primary=node3, replicas=[node1, node2]
   ... (for all 50 chunks)

10. Insert into database:
    INSERT INTO files (file_id, filename, file_size, checksum, ...)
    INSERT INTO chunks (chunk_id, file_id, chunk_index, ...)
    
11. Send UPLOAD_PLAN back to client
```

**CLIENT SIDE (continued):**
```
12. Receive UPLOAD_PLAN
13. Split file into 50 chunks (10MB each)
14. For each chunk (in parallel):
    a. Read 10MB from file
    b. Calculate chunk checksum
    c. Connect to primary node
    d. Send CHUNK_UPLOAD message with chunk data
    e. Wait for CHUNK_ACK
    f. Update progress bar: "Uploading... 45%"
```

**NODE SIDE (for each chunk):**
```
15. Receive CHUNK_UPLOAD message
16. Extract chunk data from message
17. Verify checksum
18. Write to disk: nodes/node1/chunks/chunk_abc123.dat
19. Insert into local database:
    INSERT INTO local_chunks (chunk_id, file_path, checksum, ...)
20. Send CHUNK_ACK to client
21. Notify controller: chunk stored successfully
```

**CONTROLLER SIDE (replication):**
```
22. Receive chunk storage confirmation
23. Update chunk_locations table
24. Trigger replication to replica nodes
25. Send REPLICATE_CHUNK to node2 and node3
```

**REPLICA NODES:**
```
26. Receive REPLICATE_CHUNK from controller
27. Connect to primary node (node1)
28. Request chunk data
29. Receive and verify chunk
30. Store locally
31. Confirm to controller
```

**FINAL:**
```
32. All chunks uploaded and replicated
33. Controller marks file as COMPLETE
34. Client shows: "Upload complete! vacation.mp4 (500MB)"
```

---

**[CONTINUED IN NEXT SECTION...]**

