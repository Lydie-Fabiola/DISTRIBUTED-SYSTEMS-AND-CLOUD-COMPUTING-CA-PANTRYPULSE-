# CloudSim - Actionable Development Roadmap
**Strategic Plan for Project Enhancement**  
**Date: November 21, 2025**

---

## 🎯 ROADMAP OVERVIEW

This document provides a **prioritized, actionable roadmap** for enhancing the CloudSim project from an educational prototype to a robust, production-ready distributed storage simulator.

**Timeline:** 6-12 months  
**Effort:** 200-400 development hours  
**Team Size:** 1-3 developers  

---

## 📅 PHASE 1: SECURITY & STABILITY (Weeks 1-4)
**Priority:** CRITICAL  
**Effort:** 40-60 hours  

### Task 1.1: Replace Pickle Serialization
**Current Risk:** Arbitrary code execution vulnerability  
**Solution:** Migrate to JSON

```python
# Before (INSECURE)
import pickle
message = pickle.dumps({'action': 'REGISTER', ...})
data = pickle.loads(received_data)

# After (SECURE)
import json
message = json.dumps({'action': 'REGISTER', ...}).encode()
data = json.loads(received_data.decode())
```

**Files to Modify:**
- `CloudSim/storage_virtual_network.py` (lines 51, 64, 73, 82, 84, 161)
- `CloudSim/storage_virtual_node.py` (lines 52, 80, 84, 168, 185)

**Testing:** Verify all message types serialize/deserialize correctly

---

### Task 1.2: Implement Authentication
**Current Risk:** Unauthorized node registration  
**Solution:** Token-based authentication

```python
# config.py
import secrets
NETWORK_SECRET = secrets.token_hex(32)

# Node registration with token
def register_with_network(self):
    import hmac
    import hashlib
    
    message = {
        'action': 'REGISTER',
        'node_id': self.node_id,
        'timestamp': time.time()
    }
    
    # Generate HMAC signature
    signature = hmac.new(
        NETWORK_SECRET.encode(),
        json.dumps(message).encode(),
        hashlib.sha256
    ).hexdigest()
    
    message['signature'] = signature
    # Send message...
```

**Files to Create:**
- `config.py` - Configuration management
- `auth.py` - Authentication utilities

**Files to Modify:**
- `CloudSim/storage_virtual_network.py` - Verify signatures
- `CloudSim/storage_virtual_node.py` - Sign messages

---

### Task 1.3: Add TLS/SSL Encryption
**Current Risk:** Plaintext network communication  
**Solution:** SSL-wrapped sockets

```python
import ssl

# Server side (Network Controller)
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain('server.crt', 'server.key')
secure_socket = context.wrap_socket(self.socket, server_side=True)

# Client side (Storage Node)
context = ssl.create_default_context()
context.check_hostname = False
context.verify_mode = ssl.CERT_NONE  # For development
secure_socket = context.wrap_socket(socket.socket(), server_hostname=host)
```

**Prerequisites:**
- Generate self-signed certificates (development)
- Obtain CA-signed certificates (production)

**Files to Modify:**
- `CloudSim/storage_virtual_network.py` - Wrap server socket
- `CloudSim/storage_virtual_node.py` - Wrap client sockets

---

### Task 1.4: Input Validation
**Current Risk:** Malformed messages crash system  
**Solution:** Schema validation

```python
from jsonschema import validate, ValidationError

REGISTER_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["REGISTER"]},
        "node_id": {"type": "string", "minLength": 1, "maxLength": 64},
        "host": {"type": "string"},
        "port": {"type": "integer", "minimum": 1, "maximum": 65535},
        "capacity": {
            "type": "object",
            "properties": {
                "cpu": {"type": "integer", "minimum": 1},
                "memory": {"type": "integer", "minimum": 1},
                "storage": {"type": "integer", "minimum": 1},
                "bandwidth": {"type": "integer", "minimum": 1}
            },
            "required": ["cpu", "memory", "storage", "bandwidth"]
        }
    },
    "required": ["action", "node_id", "host", "port", "capacity"]
}

def validate_message(message, schema):
    try:
        validate(instance=message, schema=schema)
        return True
    except ValidationError as e:
        print(f"Invalid message: {e}")
        return False
```

**Dependencies:** `pip install jsonschema`

**Files to Create:**
- `schemas.py` - Message schemas

**Files to Modify:**
- `CloudSim/storage_virtual_network.py` - Validate incoming messages

---

## 📅 PHASE 2: TESTING INFRASTRUCTURE (Weeks 5-8)
**Priority:** HIGH  
**Effort:** 50-70 hours  

### Task 2.1: Unit Test Suite
**Goal:** 80%+ code coverage

```python
# tests/test_storage_node.py
import pytest
from storage_virtual_node import StorageVirtualNode

def test_chunk_generation():
    node = StorageVirtualNode("test", 4, 16, 500, 1000, "localhost", 5000)
    chunks = node._generate_chunks("file1", 100 * 1024 * 1024)
    
    assert len(chunks) == 50  # 100MB / 2MB chunks
    assert all(c.checksum for c in chunks)
    assert chunks[0].size == 2 * 1024 * 1024
    assert chunks[-1].size <= 2 * 1024 * 1024

def test_storage_capacity_check():
    node = StorageVirtualNode("test", 4, 16, 1, 1000, "localhost", 5000)  # 1GB
    
    # Should succeed
    transfer1 = node.initiate_file_transfer("f1", "file1.dat", 500 * 1024 * 1024)
    assert transfer1 is not None
    
    # Should fail (exceeds capacity)
    transfer2 = node.initiate_file_transfer("f2", "file2.dat", 600 * 1024 * 1024)
    assert transfer2 is None
```

**Test Coverage Goals:**
- `storage_virtual_node.py`: 85%
- `storage_virtual_network.py`: 80%
- `main.py`: 60%

**Files to Create:**
- `tests/test_storage_node.py`
- `tests/test_storage_network.py`
- `tests/test_file_transfer.py`
- `tests/conftest.py` (pytest fixtures)

---

### Task 2.2: Integration Tests
**Goal:** Test multi-component interactions

```python
# tests/integration/test_node_registration.py
import pytest
import time
from storage_virtual_network import StorageVirtualNetwork
from storage_virtual_node import StorageVirtualNode

def test_node_registration_flow():
    # Start network controller
    network = StorageVirtualNetwork(host='localhost', port=5555)
    time.sleep(0.5)  # Allow controller to start
    
    # Start node
    node = StorageVirtualNode("node1", 4, 16, 500, 1000, "localhost", 5555)
    time.sleep(0.5)  # Allow registration
    
    # Verify node is registered
    stats = network.get_network_stats()
    assert stats['total_nodes'] == 1
    assert stats['active_nodes'] == 1
    
    # Cleanup
    node.shutdown()
    network.shutdown()
```

**Test Scenarios:**
- Node registration and activation
- Heartbeat timeout and removal
- File transfer between nodes
- Concurrent node operations
- Graceful shutdown

---

### Task 2.3: CI/CD Pipeline
**Goal:** Automated testing on every commit

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install pytest pytest-cov jsonschema
      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

**Files to Create:**
- `.github/workflows/ci.yml`
- `requirements-dev.txt`

---

## 📅 PHASE 3: FEATURE ENHANCEMENTS (Weeks 9-16)
**Priority:** MEDIUM  
**Effort:** 80-120 hours  

### Task 3.1: Data Replication
**Goal:** Store files on multiple nodes for redundancy

```python
class StorageVirtualNetwork:
    def initiate_file_transfer_with_replication(
        self,
        source_node_id: str,
        file_name: str,
        file_size: int,
        replication_factor: int = 3
    ):
        # Select N nodes for replication
        target_nodes = self._select_replication_nodes(file_size, replication_factor)
        
        if len(target_nodes) < replication_factor:
            print(f"Warning: Only {len(target_nodes)} nodes available")
        
        # Initiate transfer to all target nodes
        transfers = []
        for node_id in target_nodes:
            transfer = self.initiate_file_transfer(
                source_node_id, node_id, file_name, file_size
            )
            if transfer:
                transfers.append((node_id, transfer))
        
        return transfers
    
    def _select_replication_nodes(self, file_size, count):
        # Select nodes with sufficient space
        eligible = [
            (nid, node) for nid, node in self.nodes.items()
            if node.total_storage - node.used_storage >= file_size
        ]
        
        # Sort by available space (descending)
        eligible.sort(key=lambda x: x[1].total_storage - x[1].used_storage, reverse=True)
        
        return [nid for nid, _ in eligible[:count]]
```

---

### Task 3.2: Load Balancing
**Goal:** Distribute files evenly across nodes

```python
class LoadBalancer:
    def __init__(self, strategy='least_loaded'):
        self.strategy = strategy
    
    def select_node(self, nodes, file_size):
        if self.strategy == 'least_loaded':
            return self._least_loaded(nodes, file_size)
        elif self.strategy == 'round_robin':
            return self._round_robin(nodes)
        elif self.strategy == 'weighted':
            return self._weighted(nodes, file_size)
    
    def _least_loaded(self, nodes, file_size):
        eligible = [n for n in nodes if n.free_space >= file_size]
        if not eligible:
            return None
        return min(eligible, key=lambda n: n.utilization_percent)
    
    def _weighted(self, nodes, file_size):
        # Weight by available bandwidth and storage
        scores = []
        for node in nodes:
            if node.free_space < file_size:
                continue
            score = (node.free_space / node.total_storage) * 0.5 + \
                    (node.available_bandwidth / node.bandwidth) * 0.5
            scores.append((score, node))
        
        if not scores:
            return None
        return max(scores, key=lambda x: x[0])[1]
```

---

## 📅 PHASE 4: PERFORMANCE OPTIMIZATION (Weeks 17-20)
**Priority:** MEDIUM  
**Effort:** 40-60 hours  

### Task 4.1: Async I/O
**Goal:** Non-blocking network operations

```python
import asyncio

class AsyncStorageVirtualNode:
    async def process_chunk_transfer_async(self, file_id, chunk_id, source_node):
        if file_id not in self.active_transfers:
            return False
        
        transfer = self.active_transfers[file_id]
        chunk = next((c for c in transfer.chunks if c.chunk_id == chunk_id), None)
        
        if not chunk:
            return False
        
        # Simulate transfer without blocking
        transfer_time = (chunk.size * 8) / self.bandwidth
        await asyncio.sleep(transfer_time)
        
        chunk.status = TransferStatus.COMPLETED
        return True
```

---

## 📅 PHASE 5: ADVANCED FEATURES (Weeks 21-24)
**Priority:** LOW  
**Effort:** 60-80 hours  

### Task 5.1: Web Dashboard
### Task 5.2: Persistent Storage (SQLite)
### Task 5.3: Raft Consensus
### Task 5.4: Docker Deployment

---

## 📊 SUCCESS METRICS

| Metric | Current | Target |
|--------|---------|--------|
| Test Coverage | 0% | 80%+ |
| Security Score | 2/10 | 8/10 |
| Performance | Baseline | 2x improvement |
| Documentation | Excellent | Maintain |
| Production Readiness | 20% | 80% |

---

**Roadmap Version:** 1.0  
**Last Updated:** November 21, 2025  
**Status:** Ready for Implementation
