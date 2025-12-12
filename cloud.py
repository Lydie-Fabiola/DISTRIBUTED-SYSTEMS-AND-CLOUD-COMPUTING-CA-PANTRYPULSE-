import bcrypt
import grpc
from concurrent import futures
from google.protobuf.timestamp_pb2 import Timestamp
import cloudsecurity_pb2
import cloudsecurity_pb2_grpc
from auth_db import init_db, verify_user, create_session, migrate_credentials_doc
import json
import time
import hashlib
import secrets

# Global user storage dictionary
user_storage = {}

class UserServiceSkeleton(cloudsecurity_pb2_grpc.UserServiceServicer):
    
    def Login(self, request, context):
        print(f'Login attempt for user: {request.login}')
        login = request.login
        pwd = request.password
        
        result, user_id = self.checkId(login, pwd)
        ts = Timestamp()
        ts.GetCurrentTime()
        
        response = cloudsecurity_pb2.LoginResponse()
        
        if result == "OK":
            # Generate session token
            token = hashlib.sha256(f"{login}{secrets.token_hex(16)}{time.time()}".encode()).hexdigest()
            
            response.result = "OK"
            response.token = token
            response.user_id = user_id
            response.expires_at.CopyFrom(ts)
            
            # Persist session (allow multiple concurrent logins)
            expires_epoch = int(time.time() + 3600)
            create_session(user_id, token, expires_epoch)

            # Update storage
            if user_id not in user_storage:
                user_storage[user_id] = {
                    "storage_limit_mb": 1024,
                    "storage_used_mb": 0,
                    "last_accessed": time.time()
                }
            else:
                user_storage[user_id]["last_accessed"] = time.time()
            
            self._save_user_storage()
        else:
            response.result = "Unauthorized"
            response.token = ""
            response.user_id = ""
            response.expires_at.CopyFrom(ts)
        
        return response
    
    def checkId(self, login, pwd):
        if verify_user(login, pwd):
            return "OK", login
        return "Unauthorized", ""
    
    def _save_user_storage(self):
        try:
            with open('user_storage.json', 'w') as f:
                json.dump(user_storage, f, indent=2)
        except Exception as e:
            print(f"ERROR saving user storage: {e}")

def run():
    """Run the main cloud service"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    init_db()
    migrate_credentials_doc()
    
    user_service = UserServiceSkeleton()
    cloudsecurity_pb2_grpc.add_UserServiceServicer_to_server(user_service, server)
    
    server.add_insecure_port('[::]:51234')
    print('Starting Cloud Server on port 51234 ...', end='')
    server.start()
    print('DONE')
    server.wait_for_termination()

if __name__ == '__main__':
    run()
