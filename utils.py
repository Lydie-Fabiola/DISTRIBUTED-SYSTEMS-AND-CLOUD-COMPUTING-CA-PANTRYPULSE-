import bcrypt
import random
import smtplib
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from params import from_email, app_password

# OTP storage dictionary
otp_cache = {}

def hash_password(password):
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), 
                         bcrypt.gensalt()).decode('utf-8')

def generate_otp():
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

import hashlib

def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode('utf-8')).hexdigest()

def send_otp(to_email, user_id: str = '') -> str:
    """Send OTP to email and store in cache"""
    if not to_email:
        return "No email provided"
    to_email = str(to_email).strip().lower()
    otp = generate_otp()
    
    prev = otp_cache.get(to_email, {})
    resend_count = 0 if not prev or (time.time() - prev.get("timestamp", 0) > 300) else prev.get("resend_count", 0)
    otp_cache[to_email] = {
        "otp_hash": _hash_code(otp),
        "timestamp": time.time(),
        "verified": False,
        "resend_count": resend_count,
        "attempt_count": 0,
        "attempt_block_until": 0,
        "user_id": str(user_id or '')
    }
    
    # Email configuration
    subject = "Your OTP Code for Cloud Security Simulator"
    body = f"""
    Your OTP code is: {otp}
    
    This code will expire in 5 minutes.
    
    If you didn't request this OTP, please ignore this email.
    """
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Primary: STARTTLS
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            print(f"Starting TLS session on smtp.gmail.com:587 .........", end='')
            server.starttls()
            print('[OK]')
            print(f"Login to server with {from_email} .........", end='')
            server.login(from_email, app_password)
            print('[OK]')
            print(f"Sending OTP to {to_email} .........", end='')
            server.send_message(msg)
            print('[OK]')
            try:
                otp_cache[to_email]["resend_count"] = otp_cache[to_email].get("resend_count", 0) + 1
            except Exception:
                pass
            return f"OTP sent to {to_email} successfully!"
    except Exception as e1:
        print(f"Failed via STARTTLS: {e1}")
        try:
            # Fallback: SSL 465
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                print(f"Connecting SMTP SSL on smtp.gmail.com:465 .........", end='')
                print('[OK]')
                print(f"Login to server with {from_email} .........", end='')
                server.login(from_email, app_password)
                print('[OK]')
                print(f"Sending OTP to {to_email} .........", end='')
                server.send_message(msg)
                print('[OK]')
                try:
                    otp_cache[to_email]["resend_count"] = otp_cache[to_email].get("resend_count", 0) + 1
                except Exception:
                    pass
                return f"OTP sent to {to_email} successfully!"
        except Exception as e2:
            print(f"Failed via SSL: {e2}")
            return f"Failed to send OTP: {e2}"

def otp_can_send(email, min_interval=60):
    if not email:
        return False, min_interval
    email = str(email).strip().lower()
    data = otp_cache.get(email)
    if not data:
        return True, 0
    elapsed = time.time() - data.get("timestamp", 0)
    if elapsed < min_interval:
        return False, int(min_interval - elapsed)
    return True, 0

def otp_resend_available(email, max_resends=5):
    if not email:
        return False, 0
    email = str(email).strip().lower()
    data = otp_cache.get(email)
    if not data:
        return True, max_resends
    if time.time() - data.get("timestamp", 0) > 300:
        return True, max_resends
    count = int(data.get("resend_count", 0))
    if count >= max_resends:
        return False, 0
    return True, max_resends - count

def verify_otp(email, otp_code, user_id: str = ''):
    """Verify OTP code"""
    email = str(email).strip().lower()
    if email not in otp_cache:
        return False
    
    otp_data = otp_cache[email]
    
    # Check if OTP is expired (5 minutes)
    if time.time() - otp_data["timestamp"] > 300:
        del otp_cache[email]
        return False
    
    # Check attempt block
    if time.time() < float(otp_data.get("attempt_block_until", 0)):
        return False
    
    # Check user binding
    if otp_data.get("user_id") and str(user_id or '') and otp_data.get("user_id") != str(user_id or ''):
        return False
    # Check if OTP matches (hashed)
    if otp_data.get("otp_hash") == _hash_code(otp_code):
        otp_data["verified"] = True
        otp_data["attempt_count"] = 0
        return True
    
    # Increment attempt count and possibly block for 30s after 5 attempts
    try:
        otp_data["attempt_count"] = int(otp_data.get("attempt_count", 0)) + 1
        if otp_data["attempt_count"] >= 5:
            otp_data["attempt_block_until"] = time.time() + 30
            otp_data["attempt_count"] = 0
    except Exception:
        pass
    return False

def verify_otp_status(email, otp_code, user_id: str = ''):
    """Verify OTP and return status dict for UI feedback"""
    email = str(email).strip().lower()
    if email not in otp_cache:
        return {"ok": False, "expired": False, "blocked": False, "retry_after": 0}
    data = otp_cache[email]
    now = time.time()
    if now - data.get("timestamp", 0) > 300:
        try:
            del otp_cache[email]
        except Exception:
            pass
        return {"ok": False, "expired": True, "blocked": False, "retry_after": 0}
    if now < float(data.get("attempt_block_until", 0)):
        return {"ok": False, "expired": False, "blocked": True, "retry_after": int(float(data.get("attempt_block_until", 0)) - now)}
    # Check user binding
    if data.get("user_id") and str(user_id or '') and data.get("user_id") != str(user_id or ''):
        return {"ok": False, "expired": False, "blocked": False, "retry_after": 0}
    if data.get("otp_hash") == _hash_code(otp_code):
        data["verified"] = True
        data["attempt_count"] = 0
        data["attempt_block_until"] = 0
        return {"ok": True, "expired": False, "blocked": False, "retry_after": 0}
    # failed attempt
    try:
        data["attempt_count"] = int(data.get("attempt_count", 0)) + 1
        if data["attempt_count"] >= 5:
            data["attempt_block_until"] = now + 30
            data["attempt_count"] = 0
            return {"ok": False, "expired": False, "blocked": True, "retry_after": 30}
    except Exception:
        pass
    return {"ok": False, "expired": False, "blocked": False, "retry_after": 0}

def check_storage_limit(user_id, file_size_mb):
    """Check if user has enough storage space"""
    from cloud import user_storage
    
    if user_id not in user_storage:
        return {"allowed": False, "reason": "User not found"}
    
    user_data = user_storage[user_id]
    new_total = user_data["storage_used_mb"] + file_size_mb
    
    if new_total > user_data["storage_limit_mb"]:
        return {
            "allowed": False,
            "reason": f"Storage limit exceeded. {user_data['storage_used_mb']}/{user_data['storage_limit_mb']} MB used",
            "available_mb": user_data["storage_limit_mb"] - user_data["storage_used_mb"]
        }
    
    return {
        "allowed": True,
        "available_mb": user_data["storage_limit_mb"] - user_data["storage_used_mb"]
    }

def update_storage_usage(user_id, file_size_mb):
    """Update user's storage usage"""
    from cloud import user_storage
    
    if user_id in user_storage:
        user_storage[user_id]["storage_used_mb"] += file_size_mb
        user_storage[user_id]["last_accessed"] = time.time()
        
        # Save to file
        with open('user_storage.json', 'w') as f:
            json.dump(user_storage, f, indent=2)
        return True
    return False

def get_storage_info(user_id):
    """Get user's storage information"""
    from cloud import user_storage
    
    if user_id in user_storage:
        return user_storage[user_id]
    return None

def create_credentials_from_ids():
    """Create credentials.doc from ids.doc if needed"""
    try:
        with open('ids.doc', 'r') as ids_file:
            lines = ids_file.readlines()
        
        credentials = []
        for line in lines:
            line = line.strip()
            if line and ',' in line:
                username, password = line.split(',')
                hashed_pwd = hash_password(password)
                credentials.append(f"{username},{hashed_pwd}")
        
        with open('credentials.doc', 'w') as cred_file:
            for cred in credentials:
                cred_file.write(cred + '\n')
        
        print(f"Created credentials.doc with {len(credentials)} users")
        return True
    except FileNotFoundError:
        print("ids.doc file not found")
        return False
    except Exception as e:
        print(f"Error creating credentials: {e}")
        return False

if __name__ == '__main__':
    # Create credentials.doc from ids.doc
    create_credentials_from_ids()
