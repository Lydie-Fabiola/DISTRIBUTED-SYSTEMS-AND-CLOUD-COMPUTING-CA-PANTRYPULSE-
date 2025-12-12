import sys
import grpc
import cloudsecurity_pb2
import cloudsecurity_pb2_grpc

def main():
    if len(sys.argv) != 3:
        print("USAGE: python client.py USERNAME PASSWORD")
        print("")
        print("Examples:")
        print("  python client.py johndoe 1234567890")
        print("  python client.py janedoe 0987654321")
        return
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    try:
        channel = grpc.insecure_channel('localhost:51234')
        stub = cloudsecurity_pb2_grpc.UserServiceStub(channel)
        
        request = cloudsecurity_pb2.LoginRequest()
        request.login = username
        request.password = password
        
        response = stub.Login(request)
        
        print("")
        print("RESULT: " + response.result)
        if response.user_id:
            print("USER ID: " + response.user_id)
        if response.token:
            print("TOKEN: " + response.token[:30] + "...")
        print("")
        
    except Exception as e:
        print("ERROR: " + str(e))
        print("Make sure server is running: python start_simple.py")

if __name__ == '__main__':
    main()
