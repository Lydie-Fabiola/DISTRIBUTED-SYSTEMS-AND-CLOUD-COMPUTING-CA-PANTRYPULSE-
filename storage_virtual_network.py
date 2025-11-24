import time
import socket
import threading
import pickle
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class NetworkController(threading.Thread):
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.nodes = {}
        self.lock = threading.Lock()
        self.running = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.heartbeat_timeout = 5
        self.transfer_operations = defaultdict(dict)
        
    def run(self):
        self.running = True
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen()
            print(f"[Network] Controller started on {self.host}:{self.port}")
            
            while self.running:
                try:
                    conn, addr = self.socket.accept()
                    threading.Thread(
                        target=self._handle_connection,
                        args=(conn,),
                        daemon=True
                    ).start()
                except OSError as e:
                    if self.running:
                        print(f"[Network] Accept error: {e}")
                    break
        except OSError as e:
            print(f"[Network] Failed to start: {e}")
        finally:
            self.socket.close()
            
    def _handle_connection(self, conn):
        try:
            data = conn.recv(4096)
            if not data:
                return

            message = pickle.loads(data)
            with self.lock:
                if message['action'] == 'REGISTER':
                    node_id = message['node_id']
                    if node_id not in self.nodes:
                        print(f"[Network] Node {node_id} registered (came ONLINE)")
                    self.nodes[node_id] = {
                        'host': message['host'],
                        'port': message['port'],
                        'capacity': message['capacity'],
                        'last_seen': 0,  # 0 means registered but not yet active
                        'status': 'registered'
                    }
                    conn.sendall(pickle.dumps({'status': 'OK'}))

                elif message['action'] == 'ACTIVE_NOTIFICATION':
                    node_id = message['node_id']
                    if node_id in self.nodes:
                        if self.nodes[node_id]['status'] != 'active':
                            print(f"[Network] Node {node_id} is now ACTIVE")
                        self.nodes[node_id]['status'] = 'active'
                        self.nodes[node_id]['last_seen'] = time.time()
                        conn.sendall(pickle.dumps({'status': 'ACK'}))

                elif message['action'] == 'HEARTBEAT':
                    node_id = message['node_id']
                    if node_id in self.nodes:
                        if self.nodes[node_id]['status'] == 'registered':
                            print(f"[Network] Node {node_id} is now ACTIVE")
                            self.nodes[node_id]['status'] = 'active'
                        self.nodes[node_id]['last_seen'] = time.time()
                        conn.sendall(pickle.dumps({'status': 'ACK'}))
                    else:
                        conn.sendall(pickle.dumps({
                            'status': 'ERROR',
                            'error': 'Node not registered'
                        }))
        except Exception as e:
            print(f"[Network] Connection error: {e}")
        finally:
            conn.close()

    def check_node_status(self):
        """Check which nodes are offline"""
        current_time = time.time()
        offline_nodes = []

        with self.lock:
            for node_id, info in list(self.nodes.items()):
                if info['status'] == 'registered':
                    continue  # New node not yet active
                    
                if current_time - info['last_seen'] > self.heartbeat_timeout:
                    offline_nodes.append(node_id)
                    print(f"[Network] Node {node_id} went OFFLINE")
                    del self.nodes[node_id]

        return offline_nodes

    def stop(self):
        self.running = False
        # Create temporary connection to unblock accept()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
        except:
            pass

class StorageVirtualNetwork:
    def __init__(self, host: str = '0.0.0.0', port: int = 5000):
        self.controller = NetworkController(host, port)
        self.controller.start()
        self.heartbeat_checker = threading.Thread(
            target=self._check_heartbeats,
            daemon=True
        )
        self.heartbeat_checker.start()
        
    def _check_heartbeats(self):
        while self.controller.running:
            self.controller.check_node_status()
            time.sleep(1)
            
    def add_node(self, node_id: str, host: str, port: int, capacity: Dict):
        """Manually add a node"""
        with self.controller.lock:
            self.controller.nodes[node_id] = {
                'host': host,
                'port': port,
                'capacity': capacity,
                'last_seen': time.time(),
                'status': 'active'
            }
            print(f"[Network] Manually added node {node_id}")
            
    def connect_nodes(self, node1_id: str, node2_id: str, bandwidth: int):
        """Connect two nodes with specified bandwidth"""
        if node1_id in self.controller.nodes and node2_id in self.controller.nodes:
            self._send_connection_info(node1_id, node2_id, bandwidth)
            self._send_connection_info(node2_id, node1_id, bandwidth)
            return True
        return False
        
    def _send_connection_info(self, target_node: str, peer_node: str, bandwidth: int):
        """Send connection information to a node"""
        peer_info = self.controller.nodes[peer_node]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(2)
                s.connect((peer_info['host'], peer_info['port']))
                s.sendall(pickle.dumps({
                    'action': 'CONNECT',
                    'node_id': peer_node,
                    'host': peer_info['host'],
                    'port': peer_info['port'],
                    'bandwidth': bandwidth
                }))
            except ConnectionRefusedError:
                print(f"[Network] Could not connect to node {peer_node}")

    def get_network_stats(self) -> Dict[str, float]:
        """Get overall network statistics"""
        with self.controller.lock:
            total_bandwidth = sum(n['capacity']['bandwidth'] for n in self.controller.nodes.values())
            used_bandwidth = sum(n['capacity']['bandwidth'] * 0.5 for n in self.controller.nodes.values())  # Simulated
            total_storage = sum(n['capacity']['storage'] for n in self.controller.nodes.values())
            used_storage = sum(n['capacity']['storage'] * 0.3 for n in self.controller.nodes.values())  # Simulated
            
            return {
                "total_nodes": len(self.controller.nodes),
                "active_nodes": sum(1 for n in self.controller.nodes.values() if n['status'] == 'active'),
                "total_bandwidth_bps": total_bandwidth,
                "used_bandwidth_bps": used_bandwidth,
                "bandwidth_utilization": (used_bandwidth / total_bandwidth) * 100 if total_bandwidth > 0 else 0,
                "total_storage_bytes": total_storage,
                "used_storage_bytes": used_storage,
                "storage_utilization": (used_storage / total_storage) * 100 if total_storage > 0 else 0,
                "active_transfers": sum(len(t) for t in self.controller.transfer_operations.values())
            }

    def shutdown(self):
        """Graceful shutdown"""
        print("[Network] Shutting down controller...")
        self.controller.stop()
        self.controller.join()
        print("[Network] Controller shutdown complete")