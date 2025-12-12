import sys
import grpc
import storage_pb2
import storage_pb2_grpc

def main():
    user_id = sys.argv[1] if len(sys.argv) > 1 else 'johndoe'
    channel = grpc.insecure_channel('127.0.0.1:51236')
    stub = storage_pb2_grpc.StorageServiceStub(channel)

    data = b'Hello from demo client\n'
    put = stub.PutObject(storage_pb2.PutObjectRequest(user_id=user_id, path='demo.txt', data=data))
    print('PutObject:', put.result, put.size_mb, 'MB')

    quota = stub.GetQuota(storage_pb2.GetQuotaRequest(user_id=user_id))
    print('Quota: limit', quota.limit_mb, 'MB, used', quota.used_mb, 'MB')

    listing = stub.ListObjects(storage_pb2.ListObjectsRequest(user_id=user_id, prefix=''))
    print('ListObjects count:', len(listing.objects))
    for o in listing.objects[:5]:
        print('-', o.path, o.size_mb, 'MB')

if __name__ == '__main__':
    main()
