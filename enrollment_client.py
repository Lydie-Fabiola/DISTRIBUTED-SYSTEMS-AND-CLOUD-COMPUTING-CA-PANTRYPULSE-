import grpc
import cloudsecurity_pb2
import cloudsecurity_pb2_grpc

def test_enrollment():
    """Test the enrollment service"""
    print("Testing enrollment service...")
    try:
        with grpc.insecure_channel('localhost:51235') as channel:
            stub = cloudsecurity_pb2_grpc.EnrollmentServiceStub(channel)
            
            # Create enrollment request
            request = cloudsecurity_pb2.EnrollRequest()
            request.login = "testuser"
            request.password = "testpassword123"
            request.email = "test@example.com"
            request.full_name = "Test User"
            request.storage_limit_mb = 2048
            
            print("Sending enrollment request...")
            response = stub.Enroll(request)
            
            print(f"Response: {response.result}")
            print(f"Enrollment ID: {response.enrollment_id}")
            print(f"User ID: {response.user_id}")
            print(f"Allocated Storage: {response.allocated_storage_mb} MB")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure enrollment server is running!")

if __name__ == '__main__':
    test_enrollment()
