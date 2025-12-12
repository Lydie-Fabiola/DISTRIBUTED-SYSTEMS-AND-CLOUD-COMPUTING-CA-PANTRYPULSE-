import threading
import time
import sys

def start_system():
    print("Starting Simple Cloud Security System")
    print("=" * 50)
    
    # Try to start cloud server
    try:
        import cloud
        
        def run_cloud():
            cloud.run()
        
        cloud_thread = threading.Thread(target=run_cloud, daemon=True)
        cloud_thread.start()
        print("Cloud server started on port 51234")
    except Exception as e:
        print(f"Failed to start cloud server: {e}")
        return

    # Start enrollment server
    try:
        import enrollment

        def run_enrollment():
            enrollment.run_enrollment_server()

        enrollment_thread = threading.Thread(target=run_enrollment, daemon=True)
        enrollment_thread.start()
        print("Enrollment server started on port 51235")
    except Exception as e:
        print(f"Failed to start enrollment server: {e}")

    # Start storage server (Cloudsim)
    try:
        import storage_service

        def run_storage():
            storage_service.run_storage_server()

        storage_thread = threading.Thread(target=run_storage, daemon=True)
        storage_thread.start()
        print("Cloudsim storage server started on port 51236")
    except Exception as e:
        print(f"Failed to start storage server: {e}")

    time.sleep(2)
    
    print("")
    print("System is ready!")
    print("")
    print("Test login with:")
    print("  python client.py johndoe 1234567890")
    print("  python client.py janedoe 0987654321")
    print("")
    print("Test calculator:")
    print("  python calculator_server.py  # in another terminal")
    print("  python calculator_client.py")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == '__main__':
    start_system()
