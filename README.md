# CloudSim

CloudSim is a lightweight storage-cloud simulator that models a network controller and multiple storage nodes. It focuses on node registration, heartbeat monitoring, capacity tracking, and simulated chunk-based file transfers.

## Project Structure

| File | Description |
| --- | --- |
| `main.py` | CLI entry point. Launches either the network controller or a storage node. |
| `storage_virtual_network.py` | Implements the `NetworkController`, which tracks nodes, heartbeats, and simulated network-wide statistics. |
| `storage_virtual_node.py` | Implements `StorageVirtualNode`, including heartbeat threads, resource tracking, and simulated file transfer logic. |

## Requirements
- Python 3.9+
- No external dependencies beyond the standard library

> **Tip:** Use separate terminals for the controller and each node, since both processes are long-running loops.

## Quick Start

1. **Install Python 3.9+** (verify with `python --version`).
2. **Download/clone this repo** and open a terminal (PowerShell, Command Prompt, or Bash) in the project folder.
3. **Always run commands with `python main.py ...`**. Everything after that are options—if you miss the `python main.py` prefix, Windows treats the flags as invalid commands.
4. Use **one terminal per long-running process** (e.g., controller in Terminal A, each node in its own terminal) so you can stop them independently.
5. Press `Ctrl+C` to stop whichever process is in the active terminal.

### Step-by-step: start the controller (Terminal A)
1. Open Terminal A in the project directory.
2. Run the command on a **single line** (no `\` needed on Windows):
   ```bash
   python main.py --network --host 0.0.0.0 --network-port 5000
   ```
3. Keep this window open; it will print log messages as nodes register and send heartbeats.

### Step-by-step: start a node (Terminal B)
1. Open Terminal B in the same folder.
2. Run the node command (again, one line):
   ```bash
   python main.py --node --node-id nodeA --cpu 8 --memory 32 --storage 1000 --bandwidth 2000 --network-host localhost --network-port 5000
   ```
3. Repeat in Terminal C/D with different `--node-id` values if you want more nodes.
4. Watch Terminal A to confirm messages like `Node nodeA is now ACTIVE`.

### Simple workflow recap
1. Controller first (Terminal A).
2. Nodes afterwards (Terminal B/C/…).
3. Leave all windows running while you test.
4. Stop each window with `Ctrl+C` when done.

### Common mistakes on Windows
| Problem | Fix |
| --- | --- |
| `Unexpected token 'storage'` or similar | You probably pasted only the options. Re-run the command starting with `python main.py ...` all on one line. |
| `python` not recognized | Install Python or add it to PATH, then reopen the terminal. |
| Controller says port busy | Pick a different `--network-port` or close the process already using it. |
| Node can’t register | Ensure controller is running and `--network-host` matches its host/IP. |

## Detailed Project Explanation

### What This Project Simulates
CloudSim mirrors real distributed cloud-storage services (Google Drive, Dropbox, Amazon S3) where files are split across many nodes to improve performance, reliability, and capacity. Instead of one giant machine doing all the work, numerous smaller nodes collaborate while a central controller coordinates them.

### Project Goals
1. Show **distributed coordination** between many storage nodes and a controller.
2. Demonstrate **file chunking** and chunk metadata tracking.
3. Simulate **load balancing** decisions driven by node capacity.
4. Practice **fault tolerance** concepts via heartbeat monitoring and node removal.
5. Exercise **network communication** using Python sockets (TCP + UDP).
6. Track **resource utilization** (CPU, memory, storage, bandwidth, transfer metrics).

### Architecture Overview

#### 1. Network Controller (`StorageVirtualNetwork`)
```
┌───────────────────────────────────────────────┐
│               Network Controller              │
│                                               │
│  ┌────────────────┐   ┌───────────────────┐   │
│  │ Node Registry  │   │ Heartbeat Monitor │   │
│  │ nodeA: ACTIVE  │   │ last_seen: nodeA  │   │
│  │ nodeB: ACTIVE  │   │           nodeB   │   │
│  │ nodeC: OFFLINE │   │           nodeC   │   │
│  └────────────────┘   └───────────────────┘   │
│                                               │
│  ┌──────────────────────────────────────────┐ │
│  │        Aggregated Network Stats          │ │
│  │  total nodes, total storage, bandwidth   │ │
│  │  simulated utilization percentage        │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```
**Responsibilities**
- Accept incoming TCP connections and decode pickled messages.
- Handle registration (`REGISTER`), activation (`ACTIVE_NOTIFICATION`), and heartbeat (`HEARTBEAT`) actions.
- Maintain node metadata (host/port, capacities, status, last heartbeat).
- Periodically evict nodes that miss heartbeats for more than 5 seconds.
- Provide helper APIs to connect nodes and report network-wide metrics.

#### 2. Storage Nodes (`StorageVirtualNode`)
```
┌───────────────────────────────────────────────┐
│                Storage Node (nodeA)           │
│                                               │
│  ┌──────────────┐    ┌──────────────────────┐ │
│  │ Resources    │    │ Stored File Chunks   │ │
│  │ CPU: 8 cores │    │ fileX_chunk_0        │ │
│  │ RAM: 32 GB   │    │ fileX_chunk_1        │ │
│  │ Storage: 1TB │    │ fileY_chunk_3        │ │
│  │ BW: 2 Gbps   │    │ ...                  │ │
│  └──────────────┘    └──────────────────────┘ │
│                                               │
│  ┌──────────────────────────────────────────┐ │
│  │ Network Threads                           │ │
│  │ - Heartbeat server (UDP)                  │ │
│  │ - Heartbeat sender (TCP)                  │ │
│  │ - Registration + active notification      │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```
**Responsibilities**
- Start a UDP heartbeat server to respond to controller probes.
- Start a TCP heartbeat sender thread that pings the controller every 2 seconds.
- Register capacity info and mark itself active.
- Keep track of ongoing file transfers, chunk metadata, bandwidth usage, and stored files.
- Provide APIs to initiate transfers, process chunks, retrieve files, and expose metrics.

#### 3. File Transfer Flow (Simulated)
1. A node receives a request to store a file via `initiate_file_transfer`.
2. File size determines chunk size (512KB, 2MB, or 10MB). The node creates `FileChunk` objects with checksums.
3. Transfer metadata is stored in `active_transfers` until all chunks complete.
4. For each chunk, `process_chunk_transfer` simulates bandwidth usage (based on node bandwidth and connection bandwidth) and marks the chunk as complete.
5. Once all chunks complete, the file is moved to `stored_files`, storage metrics update, and the transfer record is removed from the active list.
6. Retrieval uses `retrieve_file`, which replays chunk metadata so another node can request the stored data.

### Key Python Technologies in Use

| Concept | Where it appears |
| --- | --- |
| `socket` (TCP/UDP) | Controller accepts connections, nodes register, heartbeats run over TCP/UDP. |
| `threading.Thread` | Controller connection handlers, heartbeat threads, background monitors. |
| `dataclasses` | `FileChunk`, `FileTransfer` models store metadata cleanly. |
| `pickle` | Lightweight serialization of Python dicts/messages over the network. |
| `hashlib` | Generates deterministic chunk checksums for validation. |
| `math`, `time` | Chunk calculations, simulated transfer delays, metrics timestamps. |

#### Example: simplified heartbeat sender (Python)
```python
class HeartbeatSender(threading.Thread):
    def run(self):
        while self.running:
            try:
                with socket.create_connection((self.network_host, self.network_port), timeout=2) as conn:
                    message = pickle.dumps({"action": "HEARTBEAT", "node_id": self.node_id})
                    conn.sendall(message)
                    response = pickle.loads(conn.recv(1024))
                    if response.get("status") != "ACK":
                        print("Heartbeat rejected", response)
            except OSError as exc:
                print("Heartbeat error:", exc)
            time.sleep(self.interval)
```

### Skills & Learning Path

| Level | Focus Areas |
| --- | --- |
| **Beginner** | Core Python syntax, functions, modules, virtual environments, basic OOP. |
| **Intermediate** | Dataclasses, typing, error handling, file I/O, simple socket clients/servers. |
| **Advanced** | Multithreading, synchronization, TCP/UDP networking patterns, serialization, distributed-system concepts (heartbeats, load balancing, failover). |

Suggested progression:
1. **Months 0‑2:** Python basics + OOP + modules.
2. **Months 2‑4:** Build small socket apps (chat server), learn threading, practice with `queue.Queue` and `threading.Lock`.
3. **Months 4‑6:** Implement multi-client servers, heartbeat monitors, serialization strategies, and logging.
4. **Months 6+ (optional):** Dive into distributed algorithms, CAP theorem, eventual consistency, and performance tuning.

### Critical Knowledge for This Project

- **Multithreading:** separate threads keep the controller responsive while monitoring heartbeats.
- **Network Programming:** both TCP (controller/node messaging) and UDP (node heartbeat server) are in play.
- **Concurrent Data Structures:** thread-safe dictionaries, locks, and queues (if extended) prevent race conditions.
- **Serialization:** nodes and controller exchange Python objects via `pickle`; alternative protocols like JSON or Protobuf can be plugged in later.
- **Distributed-systems patterns:** registration, heartbeats, failure detection, and capacity-based decisions are foundational ideas.

### Recommended Resources (Python-focused)
1. *Python Crash Course* (Eric Matthes) – fundamentals.
2. *Beej's Guide to Network Programming* – language-agnostic but excellent for sockets.
3. *Python Cookbook* (Beazley & Jones) – threading and networking recipes.
4. MIT 6.824 lectures (for high-level distributed systems concepts).
5. Real Python tutorials on sockets and concurrency.

### Bottom Line
- Expect to spend **4–6 months** reaching comfort with networking + threading if starting from intermediate Python.
- This codebase is a **sandbox**: extend it with real transfer protocols, persistence, monitoring dashboards, or REST APIs once the basics feel solid.
- Focus your learning path on Python networking, concurrency, and distributed-system fundamentals—those skills translate directly into this simulator.

## CLI Reference

| Option | Applies To | Description |
| --- | --- | --- |
| `--network` | controller | Launches the network controller process. |
| `--host` | controller | Address to bind the controller listener (default `0.0.0.0`). |
| `--network-port` | both | TCP port for controller listener (default `5000`). |
| `--node` | node | Launches a storage node. Requires `--node-id`. |
| `--node-id` | node | Unique identifier for the node (string). |
| `--cpu` | node | CPU capacity units (default `4`). |
| `--memory` | node | Memory capacity in GB (default `16`). |
| `--storage` | node | Storage capacity in GB (default `500`). |
| `--bandwidth` | node | Bandwidth in Mbps (default `1000`). |
| `--network-host` | node | Hostname/IP of the controller to register with (default `localhost`). |

## Runtime Behavior

### Network Controller
- Listens for node REGISTER, ACTIVE_NOTIFICATION, and HEARTBEAT requests.
- Tracks each node's host/port, advertised capacities, and last-seen timestamp.
- Runs a heartbeat checker thread that removes nodes if no heartbeat is received for 5 seconds.
- Provides helper methods in `StorageVirtualNetwork` to manually add nodes, connect nodes, and retrieve aggregate statistics (e.g., total bandwidth/storage, utilization estimates).

### Storage Nodes
- Spin up a UDP heartbeat server and a TCP heartbeat sender.
- Register with the controller, then periodically send heartbeat messages every 2 seconds.
- Maintain simulated metrics: storage usage, network utilization, active transfers, request counts, and failure counters.
- Support chunked file ingestion and retrieval through the `StorageVirtualNode` APIs (currently invoked programmatically, not via CLI).

## Example Session

1. Start controller (Terminal A):
   ```bash
   python main.py --network --host 0.0.0.0 --network-port 5000
   ```
2. Start node A (Terminal B):
   ```bash
   python main.py --node --node-id nodeA --network-host localhost --network-port 5000
   ```
3. Start node B (Terminal C):
   ```bash
   python main.py --node --node-id nodeB --cpu 16 --memory 64 \
       --storage 2000 --bandwidth 5000 --network-host localhost --network-port 5000
   ```
4. Observe controller logs to confirm nodes become `ACTIVE`.
5. Interrupt each terminal with `Ctrl+C` when finished.

## Extending the Simulator
- Add RPC/REST endpoints or CLI commands to trigger `initiate_file_transfer` and `process_chunk_transfer` between nodes.
- Persist node/file metadata to disk for restart durability.
- Enhance the network controller with routing policies or simulated congestion.

## Troubleshooting
- **"Node startup failed"**: ensure the controller is running and reachable on the specified host/port.
- **Port already in use**: either change `--network-port` for the controller or stop the process using that port.
- **Heartbeats timing out**: verify the node can reach the controller host (firewall, hostname resolution, etc.).
