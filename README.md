# KALY Drive — Cloud Template Project

KALY Drive is a simple cloud storage template composed of:
- A gRPC storage server that reads/writes files under a per‑user directory
- A Flask REST API that provides authentication, OTP verification, file operations, and billing
- A React web UI built with Vite that lets users sign in, upload, browse, open, trash/restore files, and upgrade storage

## Features
- Sign In with username (same as full name), password, and email for OTP
- OTP delivery and verification with safeguards:
  - Validity window: 5 minutes
  - Attempt block: 30 seconds after 5 failed attempts
  - Resend limit: 5, with rate‑limit feedback
- Dashboard and navigation sidebar
  - Files list with Open, Download, Move to Trash
  - Recent tab showing recently opened files
  - Trash tab with Restore and permanent Delete
  - Billing page to upgrade storage limits
- KALY Drive brand icon and avatar showing the initial of the user’s email
- Responsive layout and accessible controls (toggle eye icons for passwords)

## Architecture
- Web UI (`webui/`)
  - React + Vite, routes for Login, Sign In, Dashboard, Files, Recent, Trash, Billing, etc.
  - Uses `fetch` to call Flask API endpoints under `http://127.0.0.1:8081/api/*`
- API Server (`ui_server.py`)
  - Flask + CORS, endpoints:
    - `POST /api/login` and `POST /api/verify_login_otp`
    - `POST /api/enroll` (send OTP)
    - `POST /api/signup` (create account)
    - `GET /api/quota`, `GET /api/list`, `POST /api/upload`, `GET /api/download`, `DELETE /api/object`
    - `POST /api/storage_limit` (billing upgrade)
  - Talks to the storage server via gRPC on `127.0.0.1:51236`
- Storage Server (`storage_service.py`)
  - gRPC service implementing:
    - `PutObject`, `GetObject`, `ListObjects`, `DeleteObject`, `GetQuota`
  - Stores files under `storage/<user_id>/...` and tracks usage/quota in `user_storage.json`

## Key Files
- `storage_service.py`: gRPC storage server
- `ui_server.py`: Flask API server
- `auth_db.py`: Authentication, quota tracking, and storage limit updates
- `utils.py`: OTP helpers (generation, caching, verification, rate limiting)
- `webui/src/App.jsx`: Main UI, routes, and dashboard
- `webui/src/pages/Login.jsx`: Login flow with inline password eye
- `webui/src/pages/Signup.jsx`: Sign In (account creation) page with name/email/password and inline eye
- `webui/src/App.css`: App styles, including avatar, brand icon, password eye positioning

## OTP Behavior
- OTPs are valid for 5 minutes
- After 5 failed attempts, verification blocks for 30 seconds
- Resend limit enforced with clear messages

## Storage and Quota
- Files are stored per user under `storage/<user_id>/`
- Quota tracks `limit_mb` and `used_mb`
- Billing endpoint updates `limit_mb` for a user

## Running Guide

Prerequisites
- Python `>= 3.10`
- Node.js `>= 18`
- Pip and npm available in your PATH

Install Python dependencies
```
pip install flask flask-cors grpcio
```

Start the Storage Service
```
python storage_service.py
```
This starts gRPC on `127.0.0.1:51236`.

Start the API Server
```
python ui_server.py
```
This serves the REST API on `http://127.0.0.1:8081`.

Install Web UI and Start Dev Server
```
cd webui
npm install
npm run dev -- --host
```
Open the UI at `http://localhost:5173`.

Sign In and Test
- Open `http://localhost:5173`
- Use Login: enter name (username), password, and email; submit
- Check your OTP prompt; verify the code
- Navigate the dashboard: Upload, Files, Recent, Trash, Billing

