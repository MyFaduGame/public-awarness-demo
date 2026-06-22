# Cybersecurity Awareness POC

A simple educational application that demonstrates what information websites can automatically collect from users' devices through their browsers, and what they cannot access without explicit permission.

## Purpose

This is an **educational tool** designed to raise awareness about:
- What data websites can see automatically (browser info, approximate location, device type)
- What data websites **cannot** access without permission (contacts, photos, messages, etc.)

## Features

- ✅ QR code generation for easy mobile scanning
- ✅ Automatic collection of publicly available device/browser information
- ✅ IP-based approximate geolocation
- ✅ Clear visualization of collected data
- ✅ Educational messaging about browser privacy protections
- ✅ Simple JSON-based data storage (no database required)

## Technology Stack

- **Backend**: Python FastAPI
- **Frontend**: Pure HTML/CSS/JavaScript (no frameworks)
- **Storage**: JSON file (data.json)
- **QR Generation**: qrcode + pillow
- **Geolocation**: ip-api.com (free tier)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup Steps

1. **Navigate to the project directory**:
   ```bash
   cd cspa
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the application**:
   - Open your browser and go to: `http://localhost:8000`
   - You'll see a QR code on the home page

## Usage

1. **Start the server** using the command above
2. **Scan the QR code** with your mobile device (or click the link)
3. **Wait** while the application collects device information
4. **View the results** showing what websites can automatically detect

## What Data is Collected?

### Server-Side Collection:
- Public IP Address
- Approximate City
- Approximate Region/State
- Country
- ISP (Internet Service Provider)
- Timestamp

### Client-Side Collection:
- Device Type (Desktop/Mobile/Tablet)
- Browser Name & Version
- Operating System
- Screen Resolution
- Viewport Resolution
- Language Settings
- Timezone
- Referrer URL
- Cookies Enabled Status
- JavaScript Enabled Status
- Platform Information
- User Agent String
- Touch Support
- Color Depth

### What is NOT Collected:
❌ Phone numbers
❌ Contacts
❌ Messages (SMS, WhatsApp, etc.)
❌ Photos
❌ Files
❌ Installed applications
❌ Precise GPS location (without permission)
❌ Camera/microphone access (without permission)

## Project Structure

```
cspa/
│
├── main.py                 # FastAPI backend
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── data.json              # Auto-generated data storage
│
└── static/
    ├── style.css          # CSS styling
    ├── scan.html          # Data collection page
    └── results.html       # Results display page
```

## API Endpoints

- `GET /` - Home page with QR code
- `GET /scan` - Landing page that collects device info
- `POST /collect` - Endpoint to receive and store collected data
- `GET /results` - Display results page
- `GET /api/data` - Retrieve all collected data (JSON)

## Data Storage

All collected data is stored in `data.json` in the following format:

```json
[
  {
    "timestamp": "2026-06-21T10:30:00",
    "ip_address": "xxx.xxx.xxx.xxx",
    "city": "Example City",
    "country": "Example Country",
    "browser": "Chrome",
    "os": "Windows",
    "device_type": "Desktop",
    ...
  }
]
```

## Educational Purpose

This application is designed to educate users about:

1. **Browser Fingerprinting**: How websites can identify devices
2. **Privacy Awareness**: What data is automatically visible vs. protected
3. **Informed Consent**: Understanding what permissions actually protect

## Privacy & Security Notes

- This tool collects only **publicly available** information
- No sensitive personal data is accessed
- All data is stored locally in a JSON file
- No external tracking or analytics
- Use responsibly for educational purposes only

## Limitations

- IP geolocation is approximate (city-level, not precise GPS)
- Requires internet connection for IP geolocation API
- Free tier IP API has rate limits (check ip-api.com for details)

## Troubleshooting

**QR code not displaying?**
- Ensure all dependencies are installed
- Check that port 8000 is not blocked

**Geolocation not working?**
- Verify internet connection
- Check if ip-api.com is accessible
- Review API rate limits

**Data not saving?**
- Ensure write permissions in the project directory
- Check `data.json` file is created and writable

## License

This is an educational tool provided for learning purposes. Use responsibly and ethically.

## Disclaimer

This application is for **educational and awareness purposes only**. It demonstrates publicly available information that websites can collect. Always respect user privacy and comply with applicable privacy laws and regulations when developing real-world applications.
