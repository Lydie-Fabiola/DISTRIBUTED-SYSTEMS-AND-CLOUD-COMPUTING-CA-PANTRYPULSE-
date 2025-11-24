#!/usr/bin/env python3
"""
Network Controller Entry Point
Start the master coordinator for distributed storage
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.network_controller import NetworkController
from utils.logger import setup_logger

# Global controller instance
controller = None


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\nShutting down Network Controller...")
    if controller:
        controller.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Network Controller for Distributed Cloud Storage')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on (default: 5000)')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    logger = setup_logger('NetworkController', 'controller_data/controller.log', log_level)
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Print banner
    print("=" * 70)
    print("  DISTRIBUTED CLOUD STORAGE - NETWORK CONTROLLER")
    print("=" * 70)
    print(f"  Host: {args.host}")
    print(f"  Port: {args.port}")
    print(f"  Log Level: {args.log_level}")
    print("=" * 70)
    print()
    
    # Create and start controller
    global controller
    controller = NetworkController(host=args.host, port=args.port)
    
    try:
        controller.start()
        
        # Keep running
        print("\nNetwork Controller is running. Press Ctrl+C to stop.\n")
        
        # Print status periodically
        import time
        while True:
            time.sleep(10)
            status = controller.get_status()
            logger.info(f"Status: {status['active_nodes']} active nodes, {status['total_files']} files")
    
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        controller.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        controller.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()

