import os
import sqlite3
import time
import bcrypt

DB_PATH = os.path.join(os.getcwd(), 'kaly_drive.db')

def _conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = _conn()
    cur = con.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT, password_hash TEXT, full_name TEXT, created_at INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, user_id TEXT, created_at INTEGER, expires_at INTEGER)')
    cur.execute('CREATE TABLE IF NOT EXISTS storage (user_id TEXT PRIMARY KEY, limit_mb INTEGER, used_mb INTEGER, last_accessed INTEGER)')
    con.commit()
    con.close()

def create_user(user_id, email, password_hash, full_name):
    con = _conn()
    cur = con.cursor()
    cur.execute('INSERT OR REPLACE INTO users (id, email, password_hash, full_name, created_at) VALUES (?, ?, ?, ?, ?)', (user_id, email, password_hash, full_name, int(time.time())))
    con.commit()
    con.close()

def get_user(user_id):
    con = _conn()
    cur = con.cursor()
    cur.execute('SELECT id, email, password_hash, full_name, created_at FROM users WHERE id = ?', (user_id,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    return {'id': row[0], 'email': row[1], 'password_hash': row[2], 'full_name': row[3], 'created_at': row[4]}

def verify_user(user_id, password):
    u = get_user(user_id)
    if not u:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), u['password_hash'].encode('utf-8'))
    except Exception:
        return False

def create_session(user_id, token, expires_at):
    con = _conn()
    cur = con.cursor()
    cur.execute('INSERT OR REPLACE INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)', (token, user_id, int(time.time()), int(expires_at)))
    con.commit()
    con.close()

def list_sessions(user_id):
    con = _conn()
    cur = con.cursor()
    cur.execute('SELECT token, created_at, expires_at FROM sessions WHERE user_id = ? ORDER BY created_at DESC', (user_id,))
    rows = cur.fetchall()
    con.close()
    return [{'token': r[0], 'created_at': r[1], 'expires_at': r[2]} for r in rows]

def delete_session(token):
    con = _conn()
    cur = con.cursor()
    cur.execute('DELETE FROM sessions WHERE token = ?', (token,))
    con.commit()
    con.close()

def ensure_storage(user_id, default_limit_mb=1024):
    con = _conn()
    cur = con.cursor()
    cur.execute('SELECT user_id FROM storage WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    if not row:
        cur.execute('INSERT INTO storage (user_id, limit_mb, used_mb, last_accessed) VALUES (?, ?, ?, ?)', (user_id, int(default_limit_mb), 0, int(time.time())))
        con.commit()
    con.close()

def update_storage_limit(user_id, new_limit_mb):
    con = _conn()
    cur = con.cursor()
    cur.execute('UPDATE storage SET limit_mb = ?, last_accessed = ? WHERE user_id = ?', (int(new_limit_mb), int(time.time()), user_id))
    con.commit()
    con.close()

def get_quota(user_id):
    con = _conn()
    cur = con.cursor()
    cur.execute('SELECT limit_mb, used_mb FROM storage WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    con.close()
    if not row:
        return {'limit_mb': 0, 'used_mb': 0}
    return {'limit_mb': int(row[0]), 'used_mb': int(row[1])}

def add_used_mb(user_id, delta_mb):
    con = _conn()
    cur = con.cursor()
    cur.execute('SELECT limit_mb, used_mb FROM storage WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return False
    limit_mb, used_mb = int(row[0]), int(row[1])
    new_used = used_mb + int(delta_mb)
    if new_used > limit_mb:
        con.close()
        return False
    cur.execute('UPDATE storage SET used_mb = ?, last_accessed = ? WHERE user_id = ?', (new_used, int(time.time()), user_id))
    con.commit()
    con.close()
    return True

def subtract_used_mb(user_id, delta_mb):
    con = _conn()
    cur = con.cursor()
    cur.execute('SELECT used_mb FROM storage WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return False
    used_mb = int(row[1]) if len(row) > 1 else int(row[0])
    new_used = max(0, used_mb - int(delta_mb))
    cur.execute('UPDATE storage SET used_mb = ?, last_accessed = ? WHERE user_id = ?', (new_used, int(time.time()), user_id))
    con.commit()
    con.close()
    return True

def migrate_credentials_doc(path='credentials.doc'):
    try:
        with open(path, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
    except FileNotFoundError:
        return 0
    count = 0
    for line in lines:
        parts = line.split(',')
        if len(parts) >= 2:
            user_id = parts[0]
            password_hash = parts[1]
            create_user(user_id, '', password_hash, '')
            count += 1
    return count
