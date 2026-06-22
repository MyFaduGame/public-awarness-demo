from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import qrcode
from io import BytesIO
import base64
import json
from datetime import datetime
from pathlib import Path
import httpx

app = FastAPI(title="Cybersecurity Awareness POC")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Data file path
DATA_FILE = Path("data.json")

def load_data():
    """Load data from JSON file"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    """Save data to JSON file"""
    existing_data = load_data()
    existing_data.append(data)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)

async def get_ip_info(ip: str):
    """Get location information from IP address"""
    try:
        # Using free ip-api.com service
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://ip-api.com/json/{ip}")
            if response.status_code == 200:
                data = response.json()
                return {
                    "city": data.get("city", "Unknown"),
                    "region": data.get("regionName", "Unknown"),
                    "country": data.get("country", "Unknown"),
                    "isp": data.get("isp", "Unknown")
                }
    except Exception as e:
        print(f"Error fetching IP info: {e}")

    return {
        "city": "Unknown",
        "region": "Unknown",
        "country": "Unknown",
        "isp": "Unknown"
    }

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with QR code"""
    # Generate QR code for scan endpoint
    qr_url = "https://public-awarness-demo.onrender.com/scan"

    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cybersecurity Awareness - QR Demo</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 Cybersecurity Awareness Demo</h1>
                <p class="subtitle">Educational Tool - Privacy Awareness</p>
            </div>

            <div class="qr-section">
                <h2>Scan This QR Code</h2>
                <p>This demonstration will show you what information websites can automatically collect about your device.</p>

                <div class="qr-container">
                    <img src="data:image/png;base64,{img_str}" alt="QR Code" class="qr-code">
                </div>

                <div class="info-box">
                    <h3>What to expect:</h3>
                    <ul>
                        <li>✅ Browser and device information</li>
                        <li>✅ Approximate location (from IP)</li>
                        <li>✅ Screen settings and language</li>
                        <li>❌ NO personal files or contacts</li>
                        <li>❌ NO phone numbers or messages</li>
                    </ul>
                </div>

                <p class="note">Or visit: <a href="/scan">https://public-awarness-demo.onrender.com/scan</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/scan", response_class=HTMLResponse)
async def scan_page():
    """Landing page that collects device information"""
    with open("static/scan.html", "r", encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.post("/collect")
async def collect_data(request: Request):
    """Collect and store device information"""
    try:
        # Get client IP
        client_ip = request.client.host

        # Get data from request body
        body = await request.json()

        # Get IP location info
        ip_info = await get_ip_info(client_ip)

        # Combine all data
        collected_data = {
            "timestamp": datetime.now().isoformat(),
            "ip_address": client_ip,
            "city": ip_info["city"],
            "region": ip_info["region"],
            "country": ip_info["country"],
            "isp": ip_info["isp"],
            "browser": body.get("browser", "Unknown"),
            "browser_version": body.get("browser_version", "Unknown"),
            "os": body.get("os", "Unknown"),
            "device_type": body.get("device_type", "Unknown"),
            "screen_resolution": body.get("screen_resolution", "Unknown"),
            "viewport_resolution": body.get("viewport_resolution", "Unknown"),
            "language": body.get("language", "Unknown"),
            "timezone": body.get("timezone", "Unknown"),
            "referrer": body.get("referrer", "None"),
            "cookies_enabled": body.get("cookies_enabled", False),
            "javascript_enabled": True,
            "platform": body.get("platform", "Unknown"),
            "user_agent": body.get("user_agent", "Unknown"),
            "touch_support": body.get("touch_support", False),
            "color_depth": body.get("color_depth", "Unknown")
        }

        # Save to file
        save_data(collected_data)

        return JSONResponse(content={
            "status": "success",
            "data": collected_data
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )

@app.get("/results", response_class=HTMLResponse)
async def results_page():
    """Display results page"""
    with open("static/results.html", "r", encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/api/data")
async def get_all_data():
    """Get all collected data"""
    data = load_data()
    return JSONResponse(content=data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
