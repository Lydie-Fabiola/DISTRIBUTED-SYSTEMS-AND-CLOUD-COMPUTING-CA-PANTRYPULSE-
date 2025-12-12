import os
import io
import time
import shutil
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import grpc
import storage_pb2
import storage_pb2_grpc
from utils import send_otp, verify_otp_status, hash_password, otp_can_send, otp_resend_available
import secrets
from auth_db import init_db, verify_user, get_user, list_sessions, delete_session, create_user, ensure_storage, update_storage_limit
import json


app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app, resources={r"/api/*": {"origins": "*"}})


def get_storage_stub():
    channel = grpc.insecure_channel('127.0.0.1:51236')
    return storage_pb2_grpc.StorageServiceStub(channel)

# HTTP-first enroll/signup; no gRPC under the hood for these endpoints

def get_user_stub():
    channel = grpc.insecure_channel('127.0.0.1:51234')
    return cloudsecurity_pb2_grpc.UserServiceStub(channel)

init_db()


@app.get('/api/quota')
def api_quota():
    user_id = request.args.get('user_id', '')
    stub = get_storage_stub()
    quota = stub.GetQuota(storage_pb2.GetQuotaRequest(user_id=user_id))
    total, used, free = shutil.disk_usage(os.getcwd())
    return jsonify({
        'limit_mb': quota.limit_mb,
        'used_mb': quota.used_mb,
        'remaining_mb': max(quota.limit_mb - quota.used_mb, 0),
        'system_total_mb': total // (1024 * 1024),
        'system_used_mb': (total - free) // (1024 * 1024),
        'system_free_mb': free // (1024 * 1024),
    })

@app.post('/api/login')
def api_login():
    data = request.get_json(force=True)
    user_id = str(data.get('login', '')).strip()
    password = str(data.get('password', '')).strip()
    ok = verify_user(user_id, password)
    if not ok:
        return jsonify({'result':'Unauthorized'}), 401
    u = get_user(user_id)
    return jsonify({'result':'OK','user_id':user_id,'full_name':u.get('full_name',''),'email':u.get('email','')})

@app.post('/api/login_rpc')
def api_login_rpc():
    data = request.get_json(force=True)
    login = data.get('login','')
    password = data.get('password','')
    stub = get_user_stub()
    resp = stub.Login(cloudsecurity_pb2.LoginRequest(login=login, password=password))
    if resp.result != 'OK':
        return jsonify({'result':'Unauthorized'}), 401
    return jsonify({'result':'OK','user_id':resp.user_id,'token':resp.token,'expires_at':int(time.time()+3600)})

@app.post('/api/enroll')
def api_enroll_email_only():
    data = request.get_json(force=True)
    email = data.get('email','')
    user_id = data.get('user_id','')
    ok, wait = otp_can_send(email, min_interval=60)
    if not ok:
        return jsonify({'result':'RATE_LIMITED','retry_after': wait}), 429
    ok2, remaining = otp_resend_available(email, max_resends=5)
    if not ok2:
        return jsonify({'result':'RESEND_LIMIT_REACHED','message':'You have reached the maximum number of resends (5). Please wait for the code to expire.'}), 429
    msg = send_otp(email, user_id=user_id)
    resp = {'result':'OTP_REQUIRED','message':msg}
    return jsonify(resp)

@app.post('/api/verify_login_otp')
def api_verify_login_otp():
    data = request.get_json(force=True)
    email = data.get('email','')
    otp_code = data.get('otp_code','')
    user_id = data.get('user_id','')
    status = verify_otp_status(email, otp_code, user_id=user_id)
    if not status.get('ok'):
        if status.get('blocked'):
            return jsonify({'result':'ATTEMPT_BLOCKED','retry_after': int(status.get('retry_after', 30))}), 429
        if status.get('expired'):
            return jsonify({'result':'EXPIRED'}), 400
        return jsonify({'result':'FAILED'}), 400
    token = secrets.token_hex(32)
    expires_at = int(time.time()+3600)
    if user_id:
        try:
            create_session(user_id, token, expires_at)
        except Exception:
            pass
    return jsonify({'result':'OK','token':token,'expires_at':expires_at})

@app.post('/api/signup')
def api_signup():
    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        try:
            data = json.loads(request.data.decode('utf-8') or '{}')
        except Exception:
            data = {}
    user_id = str(data.get('login','')).strip()
    password = str(data.get('password','')).strip()
    email = str(data.get('email','')).strip()
    full_name = data.get('full_name','')
    limit = int(data.get('storage_limit_mb',1024))
    if not user_id or not password or not email:
        return jsonify({'result':'FAILED','message':'Missing required fields','received':data}), 400
    pwd_hash = hash_password(password)
    try:
        create_user(user_id, email, pwd_hash, full_name)
    except Exception as e:
        return jsonify({'result':'FAILED','message':str(e)}), 400
    ensure_storage(user_id, default_limit_mb=limit)
    return jsonify({'result':'SUCCESS','user_id':user_id,'allocated_storage_mb':limit})

@app.post('/api/storage_limit')
def api_storage_limit():
    data = request.get_json(force=True)
    user_id = str(data.get('user_id','')).strip()
    new_limit = int(data.get('limit_mb',0))
    if not user_id or new_limit <= 0:
        return jsonify({'result':'FAILED','message':'Invalid parameters'}), 400
    try:
        update_storage_limit(user_id, new_limit)
        return jsonify({'result':'SUCCESS','user_id':user_id,'limit_mb':new_limit})
    except Exception as e:
        return jsonify({'result':'FAILED','message':str(e)}), 400

@app.post('/api/debug_signup')
def api_debug_signup():
    return jsonify({
        'form': request.form.to_dict(),
        'json': (request.get_json(silent=True) or {}),
        'data': request.data.decode('utf-8')
    })


@app.get('/api/list')
def api_list():
    user_id = request.args.get('user_id', '')
    prefix = request.args.get('prefix', '')
    stub = get_storage_stub()
    resp = stub.ListObjects(storage_pb2.ListObjectsRequest(user_id=user_id, prefix=prefix))
    return jsonify({'objects': [{'path': o.path, 'size_mb': o.size_mb} for o in resp.objects]})


@app.post('/api/upload')
def api_upload():
    user_id = request.form.get('user_id', '')
    allow_duplicate = request.form.get('allow_duplicate', 'false') == 'true'
    path = request.form.get('path', '')
    file = request.files.get('file')
    if not file:
        return jsonify({'result': 'NoFile'}), 400

    filename = file.filename or 'upload.bin'
    final_path = path or filename
    if allow_duplicate:
        name, ext = os.path.splitext(final_path)
        final_path = f"{name}_{int(time.time()*1000)}{ext}"

    data = file.read()
    stub = get_storage_stub()
    put = stub.PutObject(storage_pb2.PutObjectRequest(user_id=user_id, path=final_path, data=data))
    return jsonify({'result': put.result, 'size_mb': int(put.size_mb), 'path': final_path})


@app.get('/api/download')
def api_download():
    user_id = request.args.get('user_id', '')
    path = request.args.get('path', '')
    stub = get_storage_stub()
    resp = stub.GetObject(storage_pb2.GetObjectRequest(user_id=user_id, path=path))
    if resp.result != 'OK':
        return jsonify({'result': resp.result}), 404
    return send_file(io.BytesIO(resp.data), as_attachment=True, download_name=os.path.basename(path))


@app.delete('/api/object')
def api_delete():
    user_id = request.args.get('user_id', '')
    path = request.args.get('path', '')
    stub = get_storage_stub()
    resp = stub.DeleteObject(storage_pb2.DeleteObjectRequest(user_id=user_id, path=path))
    return jsonify({'result': resp.result})


@app.get('/api/sessions')
def api_sessions():
    user_id = request.args.get('user_id','')
    sessions = list_sessions(user_id)
    return jsonify({'sessions': sessions})

@app.delete('/api/session')
def api_delete_session():
    token = request.args.get('token','')
    delete_session(token)
    return jsonify({'result':'OK'})


@app.get('/')
def index():
    return app.send_static_file('index.html')


def run_ui_server():
    app.run(host='0.0.0.0', port=8081, debug=False)


if __name__ == '__main__':
    run_ui_server()
