import os
import json
import time
import grpc
from concurrent import futures
import storage_pb2
import storage_pb2_grpc
from auth_db import init_db, ensure_storage, get_quota, add_used_mb, subtract_used_mb


DATA_ROOT = os.path.join(os.getcwd(), 'storage')
USER_STORAGE_FILE = os.path.join(os.getcwd(), 'user_storage.json')


def _load_user_storage():
    try:
        with open(USER_STORAGE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save_user_storage(data):
    with open(USER_STORAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _ensure_user_dir(user_id):
    path = os.path.join(DATA_ROOT, user_id)
    os.makedirs(path, exist_ok=True)
    return path


IO_EXECUTOR = futures.ThreadPoolExecutor(max_workers=50)

class StorageService(storage_pb2_grpc.StorageServiceServicer):
    def PutObject(self, request, context):
        def _do_put(req):
            init_db()
            ensure_storage(req.user_id)
            user_dir = _ensure_user_dir(req.user_id)
            target = os.path.join(user_dir, req.path)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            import math
            size_mb = math.ceil(len(req.data) / (1024 * 1024)) if len(req.data) > 0 else 0
            q = get_quota(req.user_id)
            if q['used_mb'] + size_mb > q['limit_mb']:
                return storage_pb2.PutObjectResponse(result="Storage limit exceeded", size_mb=0)
            with open(target, 'wb') as f:
                f.write(req.data)
            ok = add_used_mb(req.user_id, size_mb)
            if not ok:
                try:
                    os.remove(target)
                except OSError:
                    pass
                return storage_pb2.PutObjectResponse(result="Storage limit exceeded", size_mb=0)
            return storage_pb2.PutObjectResponse(result="OK", size_mb=size_mb)
        return IO_EXECUTOR.submit(_do_put, request).result()

    def GetObject(self, request, context):
        def _do_get(req):
            user_dir = _ensure_user_dir(req.user_id)
            target = os.path.join(user_dir, req.path)
            if not os.path.exists(target):
                return storage_pb2.GetObjectResponse(result="NotFound", data=b"", size_mb=0)
            with open(target, 'rb') as f:
                data = f.read()
            import math
            size_mb = math.ceil(len(data) / (1024 * 1024)) if len(data) > 0 else 0
            return storage_pb2.GetObjectResponse(result="OK", data=data, size_mb=size_mb)
        return IO_EXECUTOR.submit(_do_get, request).result()

    def ListObjects(self, request, context):
        def _do_list(req):
            user_dir = _ensure_user_dir(req.user_id)
            prefix_dir = os.path.join(user_dir, req.prefix) if req.prefix else user_dir
            objects = []
            if os.path.exists(prefix_dir):
                for root, _, files in os.walk(prefix_dir):
                    for fn in files:
                        full = os.path.join(root, fn)
                        rel = os.path.relpath(full, user_dir)
                        import math
                        sz = os.path.getsize(full)
                        size_mb = math.ceil(sz / (1024 * 1024)) if sz > 0 else 0
                        objects.append(storage_pb2.ObjectInfo(path=rel, size_mb=size_mb))
            return storage_pb2.ListObjectsResponse(objects=objects)
        return IO_EXECUTOR.submit(_do_list, request).result()

    def GetQuota(self, request, context):
        init_db()
        ensure_storage(request.user_id)
        q = get_quota(request.user_id)
        return storage_pb2.GetQuotaResponse(limit_mb=int(q['limit_mb']), used_mb=int(q['used_mb']))

    def DeleteObject(self, request, context):
        def _do_delete(req):
            user_dir = _ensure_user_dir(req.user_id)
            target = os.path.join(user_dir, req.path)
            if not os.path.exists(target):
                return storage_pb2.DeleteObjectResponse(result="NotFound")
            import math
            sz = os.path.getsize(target)
            size_mb = math.ceil(sz / (1024 * 1024)) if sz > 0 else 0
            os.remove(target)
            init_db()
            ensure_storage(req.user_id)
            subtract_used_mb(req.user_id, size_mb)
            return storage_pb2.DeleteObjectResponse(result="OK")
        return IO_EXECUTOR.submit(_do_delete, request).result()


def run_storage_server():
    os.makedirs(DATA_ROOT, exist_ok=True)
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=50))
    storage_pb2_grpc.add_StorageServiceServicer_to_server(StorageService(), server)
    server.add_insecure_port('[::]:51236')
    print('Starting Cloudsim Storage Server on port 51236 ...', end='')
    server.start()
    print('DONE')
    server.wait_for_termination()


if __name__ == '__main__':
    run_storage_server()
