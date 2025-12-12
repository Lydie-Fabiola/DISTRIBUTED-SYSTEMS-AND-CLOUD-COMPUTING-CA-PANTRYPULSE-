import bcrypt
import grpc
from concurrent import futures
import uuid
import time
import json
from google.protobuf.timestamp_pb2 import Timestamp
import cloudsecurity_pb2
import cloudsecurity_pb2_grpc
from utils import send_otp, verify_otp, hash_password
from auth_db import init_db, create_user, get_user, ensure_storage

# In-memory storage for enrollment data
enrollments = {}
user_storage = {}  # username -> storage info

# Default storage limits
DEFAULT_STORAGE_LIMIT_MB = 1024  # 1GB default

class EnrollmentServiceSkeleton(cloudsecurity_pb2_grpc.EnrollmentServiceServicer):
    
    def Enroll(self, request, context):
        """Handle enrollment requests with OTP verification"""
        print(f'New enrollment request for user: {request.login}')
        
        # Check if user already exists
        if self._user_exists(request.login):
            response = cloudsecurity_pb2.EnrollResponse()
            response.result = "FAILED"
            response.enrollment_id = ""
            response.user_id = ""
            response.allocated_storage_mb = 0
            return response
        
        # Generate enrollment ID
        enrollment_id = str(uuid.uuid4())
        
        # First enrollment request (without OTP)
        if not request.otp_code:
            # Send OTP to email
            otp_result = send_otp(request.email)
            
            # Store enrollment data
            enrollments[enrollment_id] = {
                "login": request.login,
                "password": request.password,
                "email": request.email,
                "full_name": request.full_name,
                "storage_limit_mb": request.storage_limit_mb or DEFAULT_STORAGE_LIMIT_MB,
                "status": "OTP_REQUIRED",
                "created_at": time.time(),
                "otp_sent_to": request.email
            }
            
            response = cloudsecurity_pb2.EnrollResponse()
            response.result = "OTP_REQUIRED"
            response.enrollment_id = enrollment_id
            response.user_id = ""
            response.allocated_storage_mb = 0
            return response
        
        # Verify OTP
        if not verify_otp(request.email, request.otp_code):
            response = cloudsecurity_pb2.EnrollResponse()
            response.result = "FAILED"
            response.enrollment_id = enrollment_id
            response.user_id = ""
            response.allocated_storage_mb = 0
            return response
        
        # OTP verified - complete enrollment
        hashed_password = hash_password(request.password)
        
        # Store in credentials.doc file
        try:
            with open('credentials.doc', 'a') as f:
                f.write(f"{request.login},{hashed_password}\n")
        except Exception as e:
            print(f"Error writing to credentials.doc: {e}")
            with open('credentials.doc', 'w') as f:
                f.write(f"{request.login},{hashed_password}\n")

        # Persist in SQLite users table
        try:
            create_user(request.login, request.email, hashed_password, request.full_name)
        except Exception as e:
            print(f"Error creating SQLite user: {e}")
        
        storage_limit = request.storage_limit_mb or DEFAULT_STORAGE_LIMIT_MB
        ensure_storage(request.login, default_limit_mb=storage_limit)
        
        # Update enrollment status
        enrollments[enrollment_id]["status"] = "COMPLETED"
        enrollments[enrollment_id]["completed_at"] = time.time()
        
        # Persist handled by SQLite; skip JSON save
        
        response = cloudsecurity_pb2.EnrollResponse()
        response.result = "SUCCESS"
        response.enrollment_id = enrollment_id
        response.user_id = request.login
        response.allocated_storage_mb = storage_limit
        return response
    
    def GetEnrollmentStatus(self, request, context):
        """Get status of an enrollment request"""
        enrollment_id = request.enrollment_id
        
        if enrollment_id not in enrollments:
            response = cloudsecurity_pb2.EnrollmentStatusResponse()
            response.status = cloudsecurity_pb2.FAILED
            response.details = "Enrollment not found"
            return response
        
        enrollment = enrollments[enrollment_id]
        
        # Map status string to enum
        status_map = {
            "OTP_REQUIRED": cloudsecurity_pb2.OTP_REQUIRED,
            "COMPLETED": cloudsecurity_pb2.COMPLETED,
            "PENDING": cloudsecurity_pb2.PENDING,
            "FAILED": cloudsecurity_pb2.FAILED
        }
        
        status = status_map.get(enrollment["status"], cloudsecurity_pb2.ENROLLMENT_STATUS_UNSPECIFIED)
        
        # Create timestamp
        ts = Timestamp()
        ts.FromSeconds(int(enrollment.get("created_at", time.time())))
        
        response = cloudsecurity_pb2.EnrollmentStatusResponse()
        response.status = status
        response.details = f"Enrollment for {enrollment['login']}"
        response.updated_at.CopyFrom(ts)
        response.otp_destination = enrollment.get("otp_sent_to", "")
        return response
    
    def _user_exists(self, username):
        """Check if user already exists in SQLite or credentials file"""
        try:
            u = get_user(username)
            if u:
                return True
        except Exception:
            pass
        try:
            with open('credentials.doc', 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) >= 1 and parts[0] == username:
                        return True
        except FileNotFoundError:
            pass
        return False
    
    def _save_user_storage(self):
        """Save user storage data to file"""
        try:
            with open('user_storage.json', 'w') as f:
                json.dump(user_storage, f, indent=2)
        except Exception as e:
            print(f"Error saving user storage: {e}")
    
    def _load_user_storage(self):
        """Load user storage data from file"""
        global user_storage
        try:
            with open('user_storage.json', 'r') as f:
                user_storage = json.load(f)
        except FileNotFoundError:
            user_storage = {}
            try:
                with open('credentials.doc', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(',')
                        if len(parts) >= 1:
                            username = parts[0]
                            email = parts[1] if len(parts) > 1 else ''
                            user_storage[username] = {
                                "storage_limit_mb": DEFAULT_STORAGE_LIMIT_MB,
                                "storage_used_mb": 0,
                                "last_accessed": time.time(),
                                "email": email
                            }
                print(f"Loaded {len(user_storage)} users from credentials.doc")
            except FileNotFoundError:
                print("No credentials.doc file found")

def run_enrollment_server():
    """Run the enrollment service server"""
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cloudsecurity_pb2_grpc.add_EnrollmentServiceServicer_to_server(
        EnrollmentServiceSkeleton(), server)
    server.add_insecure_port('[::]:51235')
    print('Starting Enrollment Server on port 51235 ............', end='')
    server.start()
    print('[OK]')
    server.wait_for_termination()

if __name__ == '__main__':
    # Load existing user storage
    enrollment_service = EnrollmentServiceSkeleton()
    enrollment_service._load_user_storage()
    run_enrollment_server()
