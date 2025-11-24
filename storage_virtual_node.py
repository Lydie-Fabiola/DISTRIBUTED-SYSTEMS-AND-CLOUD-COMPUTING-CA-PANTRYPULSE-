import time
import math
import socket
import threading
import random
import pickle
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from enum import Enum, auto
import hashlib

class TransferStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()

@dataclass
class FileChunk:
    chunk_id: int
    size: int  # in bytes
    checksum: str
    status: TransferStatus = TransferStatus.PENDING
    stored_node: Optional[str] = None

@dataclass
class FileTransfer:
    file_id: str
    file_name: str
    total_size: int  # in bytes
    chunks: List[FileChunk]
    status: TransferStatus = TransferStatus.PENDING
    created_at: float = time.time()
    completed_at: Optional[float] = None

class HeartbeatServer(threading.Thread):
    def __init__(self, node_id: str, port: int = 0):
        super().__init__(daemon=True)
        self.node_id = node_id
        self.port = port if port != 0 else random.randint(5001, 9999)
        self.running = True
        
    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.bind(('0.0.0.0', self.port))
                print(f"Heartbeat server running on port {self.port}")
                while self.running:
                    try:
                        data, addr = s.recvfrom(1024)
                        if data == b'PING':
                            s.sendto(pickle.dumps({
                                'node_id': self.node_id, 
                                'status': 'ALIVE'
                            }), addr)
                    except ConnectionResetError:
                        continue
            except OSError as e:
                print(f"Heartbeat server error: {e}")
                self.port = 0
                    
    def stop(self):
        self.running = False

class HeartbeatSender(threading.Thread):
    def __init__(self, node_id: str, network_host: str, network_port: int, interval: float = 2):
        super().__init__(daemon=True)
        self.node_id = node_id
        self.network_host = network_host
        self.network_port = network_port
        self.interval = interval
        self.running = True
        
    def run(self):
        while self.running:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.settimeout(2)
                    s.connect((self.network_host, self.network_port))
                    s.sendall(pickle.dumps({
                        'action': 'HEARTBEAT',
                        'node_id': self.node_id
                    }))
                    response = pickle.loads(s.recv(1024))
                    if response.get('status') != 'ACK':
                        print(f"Heartbeat failed: {response.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"Heartbeat error: {e}")
                time.sleep(self.interval)
            
    def stop(self):
        self.running = False

class StorageVirtualNode:
    def __init__(
        self,
        node_id: str,
        cpu_capacity: int,
        memory_capacity: int,
        storage_capacity: int,
        bandwidth: int,
        network_host: str = 'localhost',
        network_port: int = 5000,
        heartbeat_port: int = 0
    ):
        self.node_id = node_id
        self.cpu_capacity = cpu_capacity
        self.memory_capacity = memory_capacity
        self.total_storage = storage_capacity * 1024 ** 3
        self.bandwidth = bandwidth * 1000000
        self.network_host = network_host
        self.network_port = network_port
        
        # Resource tracking
        self.used_storage = 0
        self.active_transfers = {}
        self.stored_files = {}
        self.network_utilization = 0
        self.connections = {}
        
        # Metrics
        self.total_requests_processed = 0
        self.total_data_transferred = 0
        self.failed_transfers = 0
        
        # Initialize heartbeat components
        self.heartbeat_server = HeartbeatServer(node_id, heartbeat_port)
        self.heartbeat_server.start()
        
        # Wait for heartbeat server to initialize
        start_time = time.time()
        while self.heartbeat_server.port == 0 and time.time() - start_time < 5:
            time.sleep(0.1)
            
        if self.heartbeat_server.port == 0:
            raise RuntimeError("Failed to initialize heartbeat server")
        
        # Start heartbeat sender
        self.heartbeat_sender = HeartbeatSender(
            node_id=node_id,
            network_host=network_host,
            network_port=network_port
        )
        self.heartbeat_sender.start()
        
        # Register with network
        self._register_with_network()
        self._notify_active()

    def _register_with_network(self):
        """Register this node with the network controller"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(5)
                s.connect((self.network_host, self.network_port))
                s.sendall(pickle.dumps({
                    'action': 'REGISTER',
                    'node_id': self.node_id,
                    'host': 'localhost',
                    'port': self.heartbeat_server.port,
                    'capacity': {
                        'cpu': self.cpu_capacity,
                        'memory': self.memory_capacity,
                        'storage': self.total_storage,
                        'bandwidth': self.bandwidth
                    }
                }))
                response = pickle.loads(s.recv(4096))
                if response.get('status') != 'OK':
                    raise RuntimeError(f"Registration failed: {response.get('error', 'Unknown error')}")
                print(f"[Node {self.node_id}] Registered successfully")
            except Exception as e:
                raise RuntimeError(f"Failed to register with network: {e}")
            
    def _notify_active(self):
        """Send explicit active notification"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(3)
                s.connect((self.network_host, self.network_port))
                s.sendall(pickle.dumps({
                    'action': 'ACTIVE_NOTIFICATION',
                    'node_id': self.node_id
                }))
                response = pickle.loads(s.recv(1024))
                if response.get('status') != 'ACK':
                    print(f"[Node {self.node_id}] Active notification failed")
            except Exception as e:
                print(f"[Node {self.node_id}] Active notification error: {e}")

    def add_connection(self, node_id: str, host: str, port: int, bandwidth: int):
        """Add a network connection to another node"""
        self.connections[node_id] = {
            'host': host,
            'port': port,
            'bandwidth': bandwidth * 1000000
        }

    def _calculate_chunk_size(self, file_size: int) -> int:
        """Determine optimal chunk size based on file size"""
        if file_size < 10 * 1024 * 1024:  # < 10MB
            return 512 * 1024  # 512KB chunks
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return 2 * 1024 * 1024  # 2MB chunks
        else:
            return 10 * 1024 * 1024  # 10MB chunks

    def _generate_chunks(self, file_id: str, file_size: int) -> List[FileChunk]:
        """Break file into chunks for transfer"""
        chunk_size = self._calculate_chunk_size(file_size)
        num_chunks = math.ceil(file_size / chunk_size)
        
        chunks = []
        for i in range(num_chunks):
            fake_checksum = hashlib.md5(f"{file_id}-{i}".encode()).hexdigest()
            actual_chunk_size = min(chunk_size, file_size - i * chunk_size)
            chunks.append(FileChunk(
                chunk_id=i,
                size=actual_chunk_size,
                checksum=fake_checksum
            ))
        
        return chunks

    def initiate_file_transfer(
        self,
        file_id: str,
        file_name: str,
        file_size: int,
        source_node: Optional[str] = None
    ) -> Optional[FileTransfer]:
        """Initiate a file storage request to this node"""
        if self.used_storage + file_size > self.total_storage:
            return None
        
        chunks = self._generate_chunks(file_id, file_size)
        transfer = FileTransfer(
            file_id=file_id,
            file_name=file_name,
            total_size=file_size,
            chunks=chunks
        )
        
        self.active_transfers[file_id] = transfer
        return transfer

    def process_chunk_transfer(
        self,
        file_id: str,
        chunk_id: int,
        source_node: str
    ) -> bool:
        """Process an incoming file chunk"""
        if file_id not in self.active_transfers:
            return False
        
        transfer = self.active_transfers[file_id]
        
        try:
            chunk = next(c for c in transfer.chunks if c.chunk_id == chunk_id)
        except StopIteration:
            return False
        
        # Simulate network transfer
        chunk_size_bits = chunk.size * 8
        available_bandwidth = min(
            self.bandwidth - self.network_utilization,
            self.connections.get(source_node, {}).get('bandwidth', 0)
        )
        
        if available_bandwidth <= 0:
            return False
        
        transfer_time = chunk_size_bits / available_bandwidth
        time.sleep(transfer_time)
        
        # Update status
        chunk.status = TransferStatus.COMPLETED
        chunk.stored_node = self.node_id
        self.network_utilization += available_bandwidth * 0.8
        self.total_data_transferred += chunk.size
        
        # Check if transfer complete
        if all(c.status == TransferStatus.COMPLETED for c in transfer.chunks):
            transfer.status = TransferStatus.COMPLETED
            transfer.completed_at = time.time()
            self.used_storage += transfer.total_size
            self.stored_files[file_id] = transfer
            del self.active_transfers[file_id]
            self.total_requests_processed += 1
        
        return True

    def retrieve_file(
        self,
        file_id: str,
        destination_node: str
    ) -> Optional[FileTransfer]:
        """Initiate file retrieval to another node"""
        if file_id not in self.stored_files:
            return None
        
        file_transfer = self.stored_files[file_id]
        return FileTransfer(
            file_id=f"retr-{file_id}-{time.time()}",
            file_name=file_transfer.file_name,
            total_size=file_transfer.total_size,
            chunks=[
                FileChunk(
                    chunk_id=c.chunk_id,
                    size=c.size,
                    checksum=c.checksum,
                    stored_node=destination_node
                )
                for c in file_transfer.chunks
            ]
        )

    def get_storage_utilization(self) -> Dict[str, Union[int, float]]:
        return {
            "used_bytes": self.used_storage,
            "total_bytes": self.total_storage,
            "utilization_percent": (self.used_storage / self.total_storage) * 100,
            "files_stored": len(self.stored_files),
            "active_transfers": len(self.active_transfers)
        }

    def get_network_utilization(self) -> Dict[str, Union[int, float, List[str]]]:
        return {
            "current_utilization_bps": self.network_utilization,
            "max_bandwidth_bps": self.bandwidth,
            "utilization_percent": (self.network_utilization / self.bandwidth) * 100,
            "connections": list(self.connections.keys())
        }

    def get_performance_metrics(self) -> Dict[str, int]:
        return {
            "total_requests_processed": self.total_requests_processed,
            "total_data_transferred_bytes": self.total_data_transferred,
            "failed_transfers": self.failed_transfers,
            "current_active_transfers": len(self.active_transfers)
        }

    def shutdown(self):
        """Graceful shutdown procedure"""
        print(f"[Node {self.node_id}] Shutting down...")
        self.heartbeat_sender.stop()
        self.heartbeat_server.stop()
        self.heartbeat_sender.join()
        self.heartbeat_server.join()
        print(f"[Node {self.node_id}] Shutdown complete")