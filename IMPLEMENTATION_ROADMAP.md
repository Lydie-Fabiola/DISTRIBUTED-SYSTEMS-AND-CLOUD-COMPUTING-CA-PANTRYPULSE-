# 🚀 IMPLEMENTATION ROADMAP
## Step-by-Step Build Plan for Distributed Cloud Storage

---

## 📅 PHASE 1: CORE INFRASTRUCTURE (Week 1-2)

### **Task 1.1: Project Structure Setup**
```
CloudSim/
├── core/
│   ├── __init__.py
│   ├── network_controller.py      # Master coordinator
│   ├── storage_node.py             # Storage node implementation
│   ├── chunk_manager.py            # Chunk operations
│   └── metadata_manager.py         # Database operations
├── network/
│   ├── __init__.py
│   ├── tcp_server.py               # TCP server base class
│   ├── tcp_client.py               # TCP client base class
│   └── protocol.py                 # Message protocol definitions
├── storage/
│   ├── __init__.py
│   ├── disk_manager.py             # Physical disk operations
│   ├── chunk_storage.py            # Chunk read/write
│   └── database.py                 # SQLite wrapper
├── utils/
│   ├── __init__.py
│   ├── logger.py                   # Logging utilities
│   ├── crypto.py                   # Encryption/hashing
│   └── config.py                   # Configuration management
├── nodes/                          # Physical node directories
│   ├── node1/
│   ├── node2/
│   └── node3/
├── controller_data/                # Controller persistent data
│   └── controller.db
├── tests/
│   ├── test_network.py
│   ├── test_storage.py
│   └── test_integration.py
├── main_controller.py              # Controller entry point
├── main_node.py                    # Node entry point
├── requirements.txt
└── README.md
```

### **Task 1.2: Network Protocol Definition**
```python
# network/protocol.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json

class MessageType(Enum):
    # Node Management
    REGISTER_NODE = "REGISTER_NODE"
    REGISTER_ACK = "REGISTER_ACK"
    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    NODE_SHUTDOWN = "NODE_SHUTDOWN"
    
    # File Operations
    UPLOAD_REQUEST = "UPLOAD_REQUEST"
    UPLOAD_PLAN = "UPLOAD_PLAN"
    CHUNK_UPLOAD = "CHUNK_UPLOAD"
    CHUNK_ACK = "CHUNK_ACK"
    DOWNLOAD_REQUEST = "DOWNLOAD_REQUEST"
    DOWNLOAD_PLAN = "DOWNLOAD_PLAN"
    CHUNK_REQUEST = "CHUNK_REQUEST"
    CHUNK_DATA = "CHUNK_DATA"
    DELETE_REQUEST = "DELETE_REQUEST"
    DELETE_ACK = "DELETE_ACK"
    
    # Replication
    REPLICATE_CHUNK = "REPLICATE_CHUNK"
    REPLICATION_ACK = "REPLICATION_ACK"
    
    # Errors
    ERROR = "ERROR"

@dataclass
class Message:
    """Base message class"""
    type: MessageType
    payload: Dict[str, Any]
    timestamp: float
    message_id: str
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps({
            'type': self.type.value,
            'payload': self.payload,
            'timestamp': self.timestamp,
            'message_id': self.message_id
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return cls(
            type=MessageType(data['type']),
            payload=data['payload'],
            timestamp=data['timestamp'],
            message_id=data['message_id']
        )

# Example messages:

# 1. Node Registration
{
    "type": "REGISTER_NODE",
    "payload": {
        "node_id": "node1",
        "ip_address": "192.168.1.101",
        "port": 6001,
        "capacity": {
            "cpu_cores": 4,
            "memory_gb": 8,
            "storage_gb": 100,
            "bandwidth_mbps": 1000
        }
    },
    "timestamp": 1732185600.0,
    "message_id": "msg_abc123"
}

# 2. Upload Request
{
    "type": "UPLOAD_REQUEST",
    "payload": {
        "filename": "vacation.mp4",
        "file_size": 524288000,
        "checksum": "sha256_hash",
        "replication_factor": 3,
        "owner": "user@example.com"
    },
    "timestamp": 1732185600.0,
    "message_id": "msg_def456"
}

# 3. Upload Plan (Controller response)
{
    "type": "UPLOAD_PLAN",
    "payload": {
        "file_id": "file_xyz789",
        "chunk_size": 10485760,  # 10MB
        "chunk_count": 50,
        "chunk_assignments": [
            {
                "chunk_index": 0,
                "primary_node": "node1",
                "replica_nodes": ["node2", "node3"]
            },
            {
                "chunk_index": 1,
                "primary_node": "node2",
                "replica_nodes": ["node1", "node3"]
            }
            # ... for all 50 chunks
        ]
    },
    "timestamp": 1732185600.0,
    "message_id": "msg_ghi012"
}
```

### **Task 1.3: TCP Server/Client Base Classes**
```python
# network/tcp_server.py

import socket
import threading
import logging
from typing import Callable, Optional

class TCPServer:
    """Base TCP server for handling connections"""
    
    def __init__(self, host: str, port: int, handler: Callable):
        self.host = host
        self.port = port
        self.handler = handler
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def start(self):
        """Start the TCP server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)  # Allow 100 pending connections
        
        self.running = True
        self.logger.info(f"TCP Server started on {self.host}:{self.port}")
        
        # Start accept loop in separate thread
        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()
    
    def _accept_loop(self):
        """Accept incoming connections"""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.logger.info(f"New connection from {client_address}")
                
                # Handle each client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Accept error: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_address):
        """Handle client connection"""
        try:
            self.handler(client_socket, client_address)
        except Exception as e:
            self.logger.error(f"Client handler error: {e}")
        finally:
            client_socket.close()
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        self.logger.info("TCP Server stopped")
```

---

## 📅 PHASE 2: STORAGE NODE IMPLEMENTATION (Week 3-4)

### **Task 2.1: Disk Manager**
```python
# storage/disk_manager.py

import os
import hashlib
from pathlib import Path
from typing import Optional

class DiskManager:
    """Manages physical disk operations for a storage node"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.chunks_dir = self.base_dir / "chunks"
        self.temp_dir = self.base_dir / "temp"
        
        # Create directories
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def write_chunk(self, chunk_id: str, data: bytes) -> bool:
        """Write chunk to disk"""
        try:
            chunk_path = self.chunks_dir / f"{chunk_id}.dat"
            
            # Write to temporary file first
            temp_path = self.temp_dir / f"{chunk_id}.tmp"
            with open(temp_path, 'wb') as f:
                f.write(data)
            
            # Verify checksum
            calculated_checksum = self._calculate_checksum(temp_path)
            
            # Move to final location
            temp_path.rename(chunk_path)
            
            return True
        except Exception as e:
            logging.error(f"Failed to write chunk {chunk_id}: {e}")
            return False
    
    def read_chunk(self, chunk_id: str) -> Optional[bytes]:
        """Read chunk from disk"""
        try:
            chunk_path = self.chunks_dir / f"{chunk_id}.dat"
            with open(chunk_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Failed to read chunk {chunk_id}: {e}")
            return None
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """Delete chunk from disk"""
        try:
            chunk_path = self.chunks_dir / f"{chunk_id}.dat"
            chunk_path.unlink()
            return True
        except Exception as e:
            logging.error(f"Failed to delete chunk {chunk_id}: {e}")
            return False
    
    def get_disk_usage(self) -> dict:
        """Get disk usage statistics"""
        total_size = 0
        chunk_count = 0
        
        for chunk_file in self.chunks_dir.glob("*.dat"):
            total_size += chunk_file.stat().st_size
            chunk_count += 1
        
        return {
            'total_bytes': total_size,
            'chunk_count': chunk_count,
            'total_mb': total_size / (1024 * 1024),
            'total_gb': total_size / (1024 * 1024 * 1024)
        }
    
    @staticmethod
    def _calculate_checksum(file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
```

**[CONTINUED...]**

