import os
import json
import time
import bcrypt

print("Simple Setup for Cloud Security")
print("=" * 50)

# Check for credentials
print("\n1. Checking credentials...")
if os.path.exists('credentials.doc'):
    print("FOUND: credentials.doc")
    # Count lines
    count = 0
    with open('credentials.doc', 'r') as f:
        for line in f:
            if line.strip():
                count += 1
    print(f"Contains {count} user(s)")
else:
    print("NOT FOUND: credentials.doc")
    print("Creating from ids.doc...")
    
    if os.path.exists('ids.doc'):
        try:
            with open('ids.doc', 'r') as ids_file:
                with open('credentials.doc', 'w') as cred_file:
                    for line in ids_file:
                        line = line.strip()
                        if line and ',' in line:
                            username, password = line.split(',')
                            hashed = bcrypt.hashpw(
                                password.encode('utf-8'), 
                                bcrypt.gensalt()
                            ).decode('utf-8')
                            cred_file.write(f"{username},{hashed}\n")
            print("CREATED: credentials.doc")
        except Exception as e:
            print(f"ERROR: {e}")
    else:
        print("ERROR: ids.doc not found")
        print("Creating empty credentials.doc...")
        with open('credentials.doc', 'w') as f:
            f.write("")

# Check for user storage
print("\n2. Checking user storage...")
if not os.path.exists('user_storage.json'):
    print("Creating user_storage.json...")
    storage = {}
    
    # Add existing users
    if os.path.exists('credentials.doc'):
        with open('credentials.doc', 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) >= 1:
                        username = parts[0]
                        storage[username] = {
                            "storage_limit_mb": 1024,
                            "storage_used_mb": 0,
                            "last_accessed": time.time()
                        }
    
    with open('user_storage.json', 'w') as f:
        json.dump(storage, f, indent=2)
    
    print(f"CREATED: user_storage.json with {len(storage)} users")
else:
    print("FOUND: user_storage.json")

print("\n" + "=" * 50)
print("SETUP COMPLETE")
print("=" * 50)
print("\nTo start the system:")
print("  python start_simple.py")
print("\nTo test login:")
print("  python client.py johndoe 1234567890")
print("  python client.py janedoe 0987654321")
