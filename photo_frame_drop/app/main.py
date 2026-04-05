from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
import shutil
from datetime import datetime, timedelta
import secrets
import requests
import json
import magic
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import FileResponse

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Photo Frame Drop API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configuration from HA Add-on options
ACCESS_KEY = os.environ.get("ACCESS_KEY", "")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "digital_frame")

# Validate upload folder to prevent path traversal
if ".." in UPLOAD_FOLDER or UPLOAD_FOLDER.startswith("/"):
    UPLOAD_FOLDER = "digital_frame"

NOTIFY_ON_UPLOAD = os.environ.get("NOTIFY_ON_UPLOAD", "true").lower() == "true"
MEDIA_PATH = f"/media/{UPLOAD_FOLDER}"
SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")

# Simple session management
sessions = {}
SESSION_EXPIRY = timedelta(days=7)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


def create_session():
    session_token = secrets.token_urlsafe(32)
    sessions[session_token] = datetime.now() + SESSION_EXPIRY
    return session_token


def is_authenticated(request: Request):
    if not ACCESS_KEY:
        return True  # If no access key is set, authentication is bypassed

    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in sessions:
        return False
    if datetime.now() > sessions[session_token]:
        del sessions[session_token]
        return False
    return True


async def get_current_user(request: Request):
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return True


def notify_ha(message: str):
    if not SUPERVISOR_TOKEN:
        return False

    url = "http://supervisor/core/api/services/persistent_notification/create"
    headers = {
        "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "title": "Photo Frame Drop",
        "message": message,
        "notification_id": "photo_frame_drop",
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to notify HA: {e}")
        return False


def get_base_path(request: Request):
    return request.headers.get("X-Ingress-Path", "")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    base_path = get_base_path(request)
    if is_authenticated(request):
        return RedirectResponse(
            url=f"{base_path}/upload", status_code=status.HTTP_302_FOUND
        )
    return templates.TemplateResponse(
        "login.html", {"request": request, "base_path": base_path}
    )


@app.post("/api/login")
@limiter.limit("5/minute")
async def login(request: Request):
    form_data = await request.form()
    key = form_data.get("access_key")

    if key == ACCESS_KEY or not ACCESS_KEY:
        session_token = create_session()
        response = JSONResponse(content={"success": True})
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            max_age=int(SESSION_EXPIRY.total_seconds()),
            samesite="lax",
        )
        return response
    else:
        return JSONResponse(
            content={"success": False, "message": "Nieprawidłowy klucz"},
            status_code=401,
        )


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    base_path = get_base_path(request)
    if not is_authenticated(request):
        return RedirectResponse(url=f"{base_path}/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "upload.html", {"request": request, "base_path": base_path}
    )


@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    base_path = get_base_path(request)
    if not is_authenticated(request):
        return RedirectResponse(url=f"{base_path}/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        "success.html", {"request": request, "base_path": base_path}
    )


@app.get("/gallery", response_class=HTMLResponse)
async def gallery_page(request: Request):
    base_path = get_base_path(request)
    if not is_authenticated(request):
        return RedirectResponse(url=f"{base_path}/", status_code=status.HTTP_302_FOUND)

    # List images
    images = []
    if os.path.exists(MEDIA_PATH):
        for filename in os.listdir(MEDIA_PATH):
            if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif")):
                images.append(filename)

    # Sort by modification time, newest first
    images.sort(
        key=lambda x: os.path.getmtime(os.path.join(MEDIA_PATH, x)), reverse=True
    )

    return templates.TemplateResponse(
        "gallery.html", {"request": request, "images": images, "base_path": base_path}
    )


@app.post("/api/upload_files")
async def upload_files(request: Request, files: list[UploadFile] = File(...)):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    os.makedirs(MEDIA_PATH, exist_ok=True)

    saved_files = []
    for file in files:
        if not file.filename:
            continue

        # File size validation (needs to read content to determine size accurately, or limit request body size globally)
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            continue  # Skip files that are too large

        # MIME type validation using python-magic
        file_content = await file.read(2048)  # Read a chunk to detect mime type
        file.file.seek(0)  # Reset file pointer

        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type not in ["image/jpeg", "image/png", "image/webp", "image/gif"]:
            continue

        # Add timestamp to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
        file_path = os.path.join(MEDIA_PATH, safe_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        saved_files.append(safe_filename)

    if saved_files and NOTIFY_ON_UPLOAD:
        notify_ha(f"Dodano {len(saved_files)} nowych zdjęć do ramki!")

    return {"success": True, "files": saved_files}


@app.delete("/api/delete/{filename}")
async def delete_file(request: Request, filename: str):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    file_path = os.path.join(MEDIA_PATH, filename)

    # Simple path traversal protection
    if not os.path.abspath(file_path).startswith(os.path.abspath(MEDIA_PATH)):
        raise HTTPException(status_code=403, detail="Forbidden")

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return {"success": True}
        except Exception as e:
            return JSONResponse(
                content={"success": False, "message": str(e)}, status_code=500
            )

    return JSONResponse(
        content={"success": False, "message": "File not found"}, status_code=404
    )


@app.get("/api/image/{filename}")
async def get_image(request: Request, filename: str):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")

    file_path = os.path.join(MEDIA_PATH, filename)

    # Simple path traversal protection
    if not os.path.abspath(file_path).startswith(os.path.abspath(MEDIA_PATH)):
        raise HTTPException(status_code=403, detail="Forbidden")

    if os.path.exists(file_path):
        return FileResponse(file_path)

    raise HTTPException(status_code=404, detail="Image not found")
