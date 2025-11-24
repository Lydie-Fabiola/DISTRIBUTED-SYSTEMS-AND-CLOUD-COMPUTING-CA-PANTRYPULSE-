#!/usr/bin/env python3
"""
Storage Node Entry Point
Start a storage node (virtual machine) for distributed storage
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.storage_node import StorageNode
from utils.logger import setup_logger

# Global node instance
node = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nShutting down Storage Node...")
    if node:
        node.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Storage Node for Distributed Cloud Storage')
    parser.add_argument('--node-id', required=True, help='Unique node identifier (e.g., node_001)')
    parser.add_argument('--storage-path', default='storage', help='Base storage path (default: storage)')
    parser.add_argument('--disk-size', type=int, default=10, help='Virtual disk size in GB (default: 10)')
    parser.add_argument('--memory', type=int, default=1, help='Memory allocation in GB (default: 1)')
    parser.add_argument('--port', type=int, required=True, help='TCP port for this node')
    parser.add_argument('--controller-host', default='localhost', help='Controller hostname (default: localhost)')
    parser.add_argument('--controller-port', type=int, default=5000, help='Controller port (default: 5000)')
    parser.add_argument('--sparse', action='store_true', help='Use sparse disk (allocate on-demand)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    log_file = f"{args.storage_path}/{args.node_id}/node.log"
    logger = setup_logger('StorageNode', log_file, log_level)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print banner
    print("=" * 70)
    print("  DISTRIBUTED CLOUD STORAGE - STORAGE NODE")
    print("=" * 70)
    print(f"  Node ID: {args.node_id}")
    print(f"  Port: {args.port}")
    print(f"  Disk Size: {args.disk_size} GB")
    print(f"  Memory: {args.memory} GB")
    print(f"  Controller: {args.controller_host}:{args.controller_port}")
    print(f"  Storage Path: {args.storage_path}/{args.node_id}")
    print(f"  Disk Mode: {'Sparse (dynamic)' if args.sparse else 'Pre-allocated'}")
    print("=" * 70)
    print()
    
    # Create storage node
    global node
    node = StorageNode(
        node_id=args.node_id,
        storage_path=args.storage_path,
        disk_size_gb=args.disk_size,
        memory_gb=args.memory,
        port=args.port,
        controller_host=args.controller_host,
        controller_port=args.controller_port
    )
    
    try:
        # Initialize disk (this may take time if pre-allocated)
        if not args.sparse:
            print(f"\nCreating {args.disk_size} GB virtual disk (this may take a while)...")
        
        node.initialize_disk(sparse=args.sparse)
        
        # Start node
        node.start()
        
        print(f"\nStorage Node {args.node_id} is running. Press Ctrl+C to stop.\n")
        
        # Keep running
        import time
        while True:
            time.sleep(10)
            status = node.get_status()
            if status['file_system_stats']:
                stats = status['file_system_stats']
                logger.info(f"Status: {stats['used_blocks']}/{stats['total_blocks']} blocks used")
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        node.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        if node:
            node.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()

