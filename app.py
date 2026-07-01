# app.py - Enhanced Security Awareness Demo with QR Code Demonstrations
"""
HDFC Bank Cybersecurity Awareness Demo - QR Code Threat Demonstration
This educational tool demonstrates real threats from scanning unknown QR codes.
Shows users how QR codes can access their gallery, contacts, and other data.
All data is auto-deleted after 1 hour - for educational purposes only.
"""

import os
import json
import sqlite3
import datetime
import base64
import hashlib
import random
import string
import asyncio
from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
from io import BytesIO
import uvicorn
from typing import Optional, List

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secret key for sessions
SECRET_KEY = 'hdfc_cybersecurity_awareness_2026'

# Create templates folder if it doesn't exist
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Database setup for tracking data with auto-deletion
def init_db():
    conn = sqlite3.connect('awareness_demo.db')
    c = conn.cursor()

    # Table for collected data with timestamps
    c.execute('''CREATE TABLE IF NOT EXISTS collected_data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT UNIQUE,
                  qr_type TEXT,
                  data_type TEXT,
                  file_path TEXT,
                  collected_at TEXT,
                  expires_at TEXT,
                  ip_address TEXT,
                  device_info TEXT,
                  shown_to_user INTEGER DEFAULT 0)''')

    # Table for demonstration sessions
    c.execute('''CREATE TABLE IF NOT EXISTS demo_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT UNIQUE,
                  venue TEXT,
                  created_at TEXT,
                  completed INTEGER DEFAULT 0)''')

    conn.commit()
    conn.close()

init_db()

# In-memory storage for active sessions
active_sessions = {}

# Pydantic models
class QRScanData(BaseModel):
    session_id: str
    qr_type: str  # 'gallery' or 'contacts'

class PhotoUpload(BaseModel):
    session_id: str
    photo_data: str  # base64 encoded

class ContactScreenshot(BaseModel):
    session_id: str
    screenshot_data: str  # base64 encoded
    contact_count: Optional[int] = 0

class DemoSession(BaseModel):
    venue: str

# Background task to clean up expired data
async def cleanup_expired_data():
    """Delete data that's older than 1 hour"""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes

        conn = sqlite3.connect('awareness_demo.db')
        c = conn.cursor()

        now = datetime.datetime.now()
        c.execute("SELECT file_path FROM collected_data WHERE expires_at < ?",
                  (now.isoformat(),))
        expired_files = c.fetchall()

        # Delete expired files
        for (file_path,) in expired_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"[CLEANUP] Deleted expired file: {file_path}")
                except Exception as e:
                    print(f"[ERROR] Failed to delete {file_path}: {e}")

        # Remove from database
        c.execute("DELETE FROM collected_data WHERE expires_at < ?",
                  (now.isoformat(),))
        conn.commit()
        conn.close()

@app.on_event("startup")
async def startup_event():
    """Start background cleanup task"""
    asyncio.create_task(cleanup_expired_data())

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    """Main demonstration page with two QR codes"""
    try:
        # Get server URL (update this for production)
        server_url = "https://public-awarness-demo.onrender.com"  # Change to your production URL

        # Generate QR Code 1: Gallery Access Demo
        qr1 = qrcode.QRCode(version=1, box_size=10, border=5)
        qr1.add_data(f'{server_url}/qr/gallery')
        qr1.make(fit=True)
        img1 = qr1.make_image(fill_color="black", back_color="white")
        buffered1 = BytesIO()
        img1.save(buffered1, format="PNG")
        qr1_base64 = base64.b64encode(buffered1.getvalue()).decode()

        # Generate QR Code 2: Contacts Access Demo
        qr2 = qrcode.QRCode(version=1, box_size=10, border=5)
        qr2.add_data(f'{server_url}/qr/contacts')
        qr2.make(fit=True)
        img2 = qr2.make_image(fill_color="black", back_color="white")
        buffered2 = BytesIO()
        img2.save(buffered2, format="PNG")
        qr2_base64 = base64.b64encode(buffered2.getvalue()).decode()

        return templates.TemplateResponse(request, 'demo_home.html', {
            'qr_code_gallery': qr1_base64,
            'qr_code_contacts': qr2_base64
        })
    except Exception as e:
        print(f"Error in index route: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/qr/gallery', response_class=HTMLResponse)
async def qr_gallery(request: Request):
    """QR Code 1: Gallery access demonstration"""
    # Generate a unique session ID
    session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    active_sessions[session_id] = {
        'type': 'gallery',
        'created_at': datetime.datetime.now()
    }

    return templates.TemplateResponse(request, 'qr_gallery.html', {
        'session_id': session_id
    })

@app.get('/qr/contacts', response_class=HTMLResponse)
async def qr_contacts(request: Request):
    """QR Code 2: Contacts access demonstration"""
    # Generate a unique session ID
    session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    active_sessions[session_id] = {
        'type': 'contacts',
        'created_at': datetime.datetime.now()
    }

    return templates.TemplateResponse(request, 'qr_contacts.html', {
        'session_id': session_id
    })

@app.post('/upload_photo')
async def upload_photo(request: Request):
    """Receive photo from gallery"""
    try:
        data = await request.json()
        session_id = data.get('session_id')
        photo_data = data.get('photo_data')  # base64

        if not session_id or not photo_data:
            raise HTTPException(status_code=400, detail="Missing data")

        # Save photo temporarily
        photo_filename = f"photo_{session_id}.jpg"
        photo_path = os.path.join(UPLOADS_DIR, photo_filename)

        # Decode and save
        photo_bytes = base64.b64decode(photo_data.split(',')[1] if ',' in photo_data else photo_data)
        with open(photo_path, 'wb') as f:
            f.write(photo_bytes)

        # Store in database with 1-hour expiration
        conn = sqlite3.connect('awareness_demo.db')
        c = conn.cursor()

        now = datetime.datetime.now()
        expires_at = now + datetime.timedelta(hours=1)

        c.execute("""INSERT OR REPLACE INTO collected_data
                     (session_id, qr_type, data_type, file_path, collected_at, expires_at, ip_address)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (session_id, 'gallery', 'photo', photo_path, now.isoformat(),
                   expires_at.isoformat(), request.client.host))
        conn.commit()
        conn.close()

        return JSONResponse(content={
            'status': 'success',
            'message': 'Photo uploaded successfully',
            'reveal_url': f'/reveal/{session_id}'
        })

    except Exception as e:
        print(f"Error uploading photo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/upload_contacts_screenshot')
async def upload_contacts_screenshot(request: Request):
    """Receive contacts screenshot"""
    try:
        data = await request.json()
        session_id = data.get('session_id')
        screenshot_data = data.get('screenshot_data')  # base64
        contact_count = data.get('contact_count', 0)

        if not session_id or not screenshot_data:
            raise HTTPException(status_code=400, detail="Missing data")

        # Save screenshot temporarily
        screenshot_filename = f"contacts_{session_id}.jpg"
        screenshot_path = os.path.join(UPLOADS_DIR, screenshot_filename)

        # Decode and save
        screenshot_bytes = base64.b64decode(screenshot_data.split(',')[1] if ',' in screenshot_data else screenshot_data)
        with open(screenshot_path, 'wb') as f:
            f.write(screenshot_bytes)

        # Store in database with 1-hour expiration
        conn = sqlite3.connect('awareness_demo.db')
        c = conn.cursor()

        now = datetime.datetime.now()
        expires_at = now + datetime.timedelta(hours=1)

        c.execute("""INSERT OR REPLACE INTO collected_data
                     (session_id, qr_type, data_type, file_path, collected_at, expires_at, ip_address, device_info)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (session_id, 'contacts', 'screenshot', screenshot_path, now.isoformat(),
                   expires_at.isoformat(), request.client.host, json.dumps({'contact_count': contact_count})))
        conn.commit()
        conn.close()

        return JSONResponse(content={
            'status': 'success',
            'message': 'Contacts screenshot uploaded successfully',
            'reveal_url': f'/reveal/{session_id}'
        })

    except Exception as e:
        print(f"Error uploading contacts screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/reveal/{session_id}', response_class=HTMLResponse)
async def reveal_data(request: Request, session_id: str):
    """Reveal what was collected - THE SCARY PART"""
    conn = sqlite3.connect('awareness_demo.db')
    c = conn.cursor()

    c.execute("SELECT * FROM collected_data WHERE session_id = ?", (session_id,))
    data = c.fetchone()

    if not data:
        return templates.TemplateResponse(request, 'error.html', {
            'message': 'Session not found or expired'
        })

    # Mark as shown to user
    c.execute("UPDATE collected_data SET shown_to_user = 1 WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()

    # Parse data
    (db_id, session_id, qr_type, data_type, file_path, collected_at,
     expires_at, ip_address, device_info, shown_to_user) = data

    # Read the file and encode as base64 for display
    image_data = None
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode()

    return templates.TemplateResponse(request, 'reveal.html', {
        'qr_type': qr_type,
        'data_type': data_type,
        'image_data': image_data,
        'collected_at': collected_at,
        'expires_at': expires_at,
        'ip_address': ip_address,
        'session_id': session_id
    })

@app.get('/education', response_class=HTMLResponse)
async def education(request: Request):
    """Educational page after the scare - how to protect yourself"""
    return templates.TemplateResponse(request, 'education.html', {})

@app.get('/admin/dashboard', response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard to see all demonstrations"""
    conn = sqlite3.connect('awareness_demo.db')
    c = conn.cursor()

    c.execute("""SELECT session_id, qr_type, data_type, collected_at, expires_at,
                        shown_to_user, ip_address
                 FROM collected_data
                 ORDER BY collected_at DESC LIMIT 50""")
    records = c.fetchall()
    conn.close()

    return templates.TemplateResponse(request, 'admin_dashboard.html', {
        'records': records
    })

if __name__ == '__main__':
    print("=" * 70)
    print(" HDFC Bank - Cybersecurity Awareness Demo")
    print(" QR Code Threat Demonstration")
    print("=" * 70)
    print(" This demo shows users real threats from scanning unknown QR codes")
    print(" All collected data is AUTO-DELETED after 1 hour")
    print("=" * 70)
    print(" Access the demo at: https://public-awarness-demo.onrender.com")
    print("=" * 70)

    port = int(os.getenv('PORT', 8001))
    uvicorn.run(app, host='0.0.0.0', port=port)
