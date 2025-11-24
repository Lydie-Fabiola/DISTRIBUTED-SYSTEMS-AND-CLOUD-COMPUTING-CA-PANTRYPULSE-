# CloudSim - Master Implementation Plan
## Building a REAL Distributed Storage System from Scratch

---

## 🎯 PROJECT VISION (CONFIRMED)

You are building a **REAL distributed cloud storage system** that:

### ✅ MUST HAVE (Non-Negotiable):
1. **Physical Storage**: Files stored on actual hard drive, consuming real disk space
2. **Real IP Addresses**: Nodes bind to network interfaces with actual IPs
3. **Dynamic Nodes**: Create unlimited nodes at runtime, each independent
4. **Process Isolation**: Each node runs as separate process (like VMs)
5. **Real File Operations**: Create, delete, transfer files - no mocking
6. **OS-like Terminal**: Each node has CLI for operations
7. **No Frameworks**: Build from scratch using only Python standard library + minimal deps

### ❌ MUST NOT HAVE:
1. ❌ In-memory simulation
2. ❌ Fake/mock implementations
3. ❌ Static configurations
4. ❌ Framework abstractions

---

## 📊 CURRENT PROJECT STATUS (15% Complete)

### ✅ What You Have:
- Basic class structures (StorageVirtualNode, StorageVirtualNetwork)
- Heartbeat mechanism (CloudSim version)
- Chunk generation logic
- Documentation and architecture diagrams

### ❌ What's Missing (85%):
- **Physical file storage** (currently in-memory)
- **Real networking** (currently method calls)
- **Dynamic node creation** (currently hardcoded)
- **Metadata persistence** (no database)
- **Replication** (no redundancy)
- **Client interface** (no CLI tool)
- **Failure recovery** (basic detection only)
- **Concurrent operations** (limited threading)

---

## 🏗️ COMPLETE SYSTEM ARCHITECTURE

### Component Hierarchy

```
CloudSim/
├── core/
│   ├── storage_node.py          # Storage Node implementation
│   ├── network_controller.py    # Network Controller implementation
│   ├── chunk_manager.py         # Chunk operations
│   ├── metadata_manager.py      # Database operations
│   └── heartbeat_manager.py     # Heartbeat protocol
│
├── network/
│   ├── tcp_server.py            # TCP server for data transfer
│   ├── udp_server.py            # UDP server for heartbeats
│   ├── protocol.py              # Message protocol definitions
│   └── serialization.py         # JSON serialization
│
├── client/
│   ├── cli.py                   # Command-line interface
│   ├── api.py                   # Python API
│   └── file_operations.py       # Upload/download logic
│
├── storage/
│   ├── file_system.py           # File I/O operations
│   ├── chunk_storage.py         # Chunk persistence
│   └── database.py              # SQLite wrapper
│
├── utils/
│   ├── config.py                # Configuration management
│   ├── logger.py                # Logging utilities
│   ├── crypto.py                # Checksums, hashing
│   └── helpers.py               # Common utilities
│
├── data/                        # Runtime data directory
│   ├── controller/
│   │   ├── metadata.db
│   │   └── logs/
│   └── nodes/
│       ├── node_001/
│       │   ├── chunks/
│       │   ├── metadata.db
│       │   └── logs/
│       └── node_002/
│           └── ...
│
├── tests/
│   ├── test_storage_node.py
│   ├── test_network_controller.py
│   └── ...
│
├── scripts/
│   ├── start_controller.py      # Launch controller
│   ├── start_node.py            # Launch node
│   └── cloudsim_cli.py          # Client CLI
│
├── config/
│   ├── controller_config.yaml
│   └── node_template.yaml
│
└── docs/
    ├── API.md
    ├── PROTOCOL.md
    └── DEPLOYMENT.md
```

---

## 🔧 DETAILED COMPONENT SPECIFICATIONS

### 1. STORAGE NODE - Complete Specification

**File**: `core/storage_node.py`

**Responsibilities**:
1. Bind to network interface with real IP address
2. Store chunks as physical files on disk
3. Maintain local metadata database (SQLite)
4. Send heartbeats to controller
5. Handle chunk upload/download/delete requests
6. Monitor local resources (disk, CPU, memory)
7. Provide terminal interface for local operations

**Implementation Details**:

```python
import socket
import threading
import sqlite3
import os
import hashlib
import json
import time
from pathlib import Path

class StorageNode:
    """
    Real storage node that:
    - Runs as independent process
    - Stores chunks on physical disk
    - Has real IP address
    - Communicates via TCP/UDP
    """
    
    def __init__(self, node_id, storage_path, storage_capacity_gb, 
                 controller_host, controller_port, bind_ip='0.0.0.0', bind_port=0):
        """
        Initialize storage node
        
        Args:
            node_id: Unique identifier (e.g., 'node_001')
            storage_path: Physical directory path (e.g., '/data/cloudsim/nodes/node_001')
            storage_capacity_gb: Maximum storage in GB
            controller_host: Controller IP address
            controller_port: Controller port
            bind_ip: IP to bind to (0.0.0.0 = all interfaces)
            bind_port: Port to bind to (0 = auto-assign)
        """
        self.node_id = node_id
        self.storage_path = Path(storage_path)
        self.storage_capacity = storage_capacity_gb * 1024 * 1024 * 1024  # Convert to bytes
        self.controller_host = controller_host
        self.controller_port = controller_port
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        
        # Create directory structure
        self.chunks_dir = self.storage_path / 'chunks'
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.db_path = self.storage_path / 'metadata.db'
        self._init_database()
        
        # Network components
        self.tcp_server = None
        self.tcp_port = None  # Will be set after binding
        self.heartbeat_thread = None
        self.running = False
        
    def _init_database(self):
        """Create SQLite database for chunk metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                file_id TEXT NOT NULL,
                chunk_number INTEGER NOT NULL,
                size INTEGER NOT NULL,
                checksum TEXT NOT NULL,
                file_path TEXT NOT NULL,
                stored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS node_stats (
                timestamp TIMESTAMP PRIMARY KEY,
                total_chunks INTEGER,
                used_storage INTEGER,
                available_storage INTEGER
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def start(self):
        """Start the storage node"""
        print(f"[{self.node_id}] Starting storage node...")
        
        # 1. Start TCP server for chunk operations
        self._start_tcp_server()
        
        # 2. Register with controller
        self._register_with_controller()
        
        # 3. Start heartbeat sender
        self._start_heartbeat()
        
        # 4. Start terminal interface
        self._start_terminal()
        
    def _start_tcp_server(self):
        """Start TCP server to handle chunk operations"""
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server.bind((self.bind_ip, self.bind_port))
        self.tcp_port = self.tcp_server.getsockname()[1]  # Get actual port
        self.tcp_server.listen(5)
        
        print(f"[{self.node_id}] TCP server listening on {self.bind_ip}:{self.tcp_port}")
        
        # Start accept loop in separate thread
        self.running = True
        accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
        accept_thread.start()
        
    def _accept_connections(self):
        """Accept incoming TCP connections"""
        while self.running:
            try:
                conn, addr = self.tcp_server.accept()
                # Handle each connection in separate thread
                handler_thread = threading.Thread(
                    target=self._handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                handler_thread.start()
            except Exception as e:
                if self.running:
                    print(f"[{self.node_id}] Error accepting connection: {e}")
                    
    def _handle_client(self, conn, addr):
        """Handle client request"""
        try:
            # Receive request (JSON)
            data = conn.recv(4096).decode('utf-8')
            request = json.loads(data)
            
            action = request.get('action')
            
            if action == 'STORE_CHUNK':
                response = self._handle_store_chunk(request)
            elif action == 'RETRIEVE_CHUNK':
                response = self._handle_retrieve_chunk(request)
            elif action == 'DELETE_CHUNK':
                response = self._handle_delete_chunk(request)
            elif action == 'LIST_CHUNKS':
                response = self._handle_list_chunks()
            else:
                response = {'status': 'ERROR', 'message': 'Unknown action'}
                
            # Send response
            conn.sendall(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            error_response = {'status': 'ERROR', 'message': str(e)}
            conn.sendall(json.dumps(error_response).encode('utf-8'))
        finally:
            conn.close()
```

**Key Features**:
- ✅ Real TCP socket server
- ✅ Physical file storage
- ✅ SQLite metadata database
- ✅ Multi-threaded connection handling
- ✅ Actual IP address binding

---

### 2. NETWORK CONTROLLER - Complete Specification

**File**: `core/network_controller.py`

**Responsibilities**:
1. Maintain registry of all active nodes
2. Monitor node health via heartbeats
3. Manage file metadata (which chunks on which nodes)
4. Coordinate file uploads/downloads
5. Implement load balancing
6. Trigger replication when nodes fail
7. Provide statistics and monitoring

**Key Implementation Points**:
```python
class NetworkController:
    def __init__(self, host='0.0.0.0', port=5000, data_dir='/data/cloudsim/controller'):
        # Initialize with real database
        self.db_path = Path(data_dir) / 'metadata.db'
        self._init_database()
        
        # Node registry (in-memory cache + database)
        self.nodes = {}  # {node_id: {ip, port, capacity, last_heartbeat}}
        
        # Start TCP server for commands
        # Start UDP server for heartbeats
        # Start health checker thread
```

---

## 📋 IMPLEMENTATION PHASES

### PHASE 1: Core Infrastructure (Week 1-2)
**Goal**: Get basic node and controller running with real networking

**Tasks**:
1. ✅ Implement StorageNode with TCP server
2. ✅ Implement NetworkController with TCP/UDP servers
3. ✅ Implement node registration protocol
4. ✅ Implement heartbeat mechanism
5. ✅ Create physical directory structure
6. ✅ Initialize SQLite databases

**Deliverable**: Can start controller and multiple nodes, nodes register and send heartbeats

---

### PHASE 2: Chunk Storage (Week 3-4)
**Goal**: Store and retrieve chunks on physical disk

**Tasks**:
1. ✅ Implement chunk file I/O
2. ✅ Implement checksum verification
3. ✅ Implement metadata persistence
4. ✅ Test chunk upload/download between nodes

**Deliverable**: Can store chunks on disk and retrieve them

---

**NEXT**: Continue with remaining phases and detailed code examples.

