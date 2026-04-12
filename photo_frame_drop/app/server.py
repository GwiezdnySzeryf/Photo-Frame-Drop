"""Photo Frame Drop — aiohttp web application.

Routes
------
GET  /health               Watchdog endpoint; always returns 200 {"status":"ok"}
GET  /                     Login page (unauthenticated) or gallery (authenticated)
POST /login                Validate password, set session cookie
POST /logout               Clear session cookie
POST /upload               Accept a multipart photo upload
GET  /photos               JSON list of photos in the media folder
DELETE /photos/{filename}  Delete a specific photo
GET  /static/...           Static assets (CSS, JS)
"""

import hashlib
import logging
import os
import re
import secrets
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

import aiofiles
from aiohttp import web

from notifications import send_ha_notification

import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("photo_frame_drop.server")

_UNSAFE_CHARS = re.compile(r"[^\w\-. ]")
_executor = ThreadPoolExecutor(max_workers=2)
_SESSION_SECRET = secrets.token_urlsafe(
    32
)  # Random secret generated on startup prevents deterministic sessions

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Rate Limiting Store
_failed_logins: dict[str, list[float]] = defaultdict(list)

# Notification Debounce Store
_notify_files: list[str] = []
_notify_task: asyncio.Task | None = None

# ---------------------------------------------------------------------------- #
# Helpers                                                                       #
# ---------------------------------------------------------------------------- #


def _sanitize_filename(name: str) -> str:
    """Strip directory components and replace unsafe characters."""
    name = Path(name).name  # removes any directory prefix
    name = _UNSAFE_CHARS.sub("_", name)
    return name.strip() or "upload"


def _session_value(password: str) -> str:
    """Derive a session token combining the password and a dynamic startup secret."""
    return hashlib.sha256(f"pfd:{password}:{_SESSION_SECRET}".encode()).hexdigest()


def _is_authenticated(config: dict[str, Any], request: web.Request) -> bool:
    expected_session = _session_value(config["password"])

    # 1. Try reading from cookie
    if request.cookies.get("pfd_session") == expected_session:
        return True

    # 2. Try reading from Authorization Header (Ingress fallback)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        if token == expected_session:
            return True

    return False


def _require_auth(config: dict[str, Any], request: web.Request) -> None:
    """Raise 401 if the request is not authenticated."""
    if not _is_authenticated(config, request):
        raise web.HTTPUnauthorized(reason="Authentication required")


def _check_csrf(request: web.Request) -> None:
    """Basic CSRF protection for API endpoints."""
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        raise web.HTTPForbidden(reason="CSRF check failed (missing X-Requested-With)")


def _get_client_ip(request: web.Request) -> str:
    """Get the real client IP, even behind HA Ingress/Proxy."""
    return request.headers.get("X-Forwarded-For", request.remote).split(",")[0].strip()


def _is_rate_limited(ip: str) -> bool:
    """Check if the IP has exceeded 5 failed attempts in 5 minutes."""
    now = time.time()
    _failed_logins[ip] = [t for t in _failed_logins[ip] if now - t < 300]
    return len(_failed_logins[ip]) >= 5


def _record_failed_login(ip: str) -> None:
    """Record a failed login attempt."""
    _failed_logins[ip].append(time.time())


# ---------------------------------------------------------------------------- #
# App factory                                                                   #
# ---------------------------------------------------------------------------- #


def create_app(config: dict[str, Any]) -> web.Application:
    """Create and configure the aiohttp Application."""
    app = web.Application(client_max_size=config["max_bytes"] + 65536)
    app["config"] = config

    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_index)
    app.router.add_post("/login", handle_login)
    app.router.add_post("/logout", handle_logout)
    app.router.add_post("/upload", handle_upload)
    app.router.add_get("/photos", handle_list_photos)
    app.router.add_delete("/photos/{filename}", handle_delete_photo)
    app.router.add_get("/media/{filename}", handle_get_media)
    app.router.add_get("/thumb/{filename}", handle_get_thumb)

    if STATIC_DIR.is_dir():
        app.router.add_static("/static", STATIC_DIR, show_index=False)

    return app


# ---------------------------------------------------------------------------- #
# Route handlers                                                                #
# ---------------------------------------------------------------------------- #


def _get_base_path(request: web.Request) -> str:
    """Extract the Ingress path from the request headers."""
    return request.headers.get("X-Ingress-Path", "")


async def handle_health(request: web.Request) -> web.Response:
    """Watchdog endpoint."""
    return web.json_response({"status": "ok"})


async def handle_index(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    base_path = _get_base_path(request)

    if not _is_authenticated(config, request):
        text = (TEMPLATES_DIR / "login.html").read_text()
        text = text.replace("{{ base_path }}", base_path)
        text = text.replace(
            "{{ login_description }}", config.get("login_description", "")
        )
        return web.Response(text=text, content_type="text/html")

    text = (TEMPLATES_DIR / "index.html").read_text()
    text = text.replace("{{ base_path }}", base_path)
    return web.Response(text=text, content_type="text/html")


async def handle_login(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    base_path = _get_base_path(request)
    client_ip = _get_client_ip(request)

    if _is_rate_limited(client_ip):
        logger.warning("Rate limit exceeded for login from IP: %s", client_ip)
        return web.HTTPTooManyRequests(
            reason="Too many failed attempts. Try again in 5 minutes."
        )

    data = await request.post()
    entered: str = data.get("password", "")

    if entered == config["password"]:
        response = web.HTTPFound(f"{base_path}/")

        # W Ingress Home Assistanta ciasteczka gubią się ze względu na proxy iframe.
        # Wycofujemy się ze skomplikowanych flag `path` i restrykcji `samesite`,
        # które odrzucają ciasteczka logowania w tym środowisku, wracając do bazowego kodu.
        response.set_cookie(
            "pfd_session",
            _session_value(config["password"]),
            httponly=True,
            samesite="Strict",
            max_age=7 * 24 * 3600,
        )
        logger.info("Successful login from %s", client_ip)
        return response

    _record_failed_login(client_ip)
    logger.warning("Failed login attempt from %s", client_ip)

    if config.get("notify_on_failed_login") and config.get("supervisor_token"):
        asyncio.create_task(
            send_ha_notification(
                token=config["supervisor_token"],
                message=f"Błędna próba logowania do Photo Frame Drop z adresu IP: {client_ip}",
                title="⚠️ Alert bezpieczeństwa: Photo Frame Drop",
            )
        )

    return web.HTTPFound(f"{base_path}/?error=wrong_password")


async def handle_logout(request: web.Request) -> web.Response:
    _check_csrf(request)
    base_path = _get_base_path(request)
    response = web.json_response({"status": "logged_out"})
    response.del_cookie("pfd_session")
    return response


async def _send_debounced_notification(token: str, message: str) -> None:
    try:
        await asyncio.sleep(2.0)
    except asyncio.CancelledError:
        return

    count = len(_notify_files)
    if count == 1:
        msg = f"{message} [{_notify_files[0]}]"
    elif count > 1:
        msg = f"{message} ({count} photos)"
    else:
        return

    _notify_files.clear()
    await send_ha_notification(token=token, message=msg)


async def handle_upload(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)
    _check_csrf(request)

    reader = await request.multipart()
    field = await reader.next()
    while field is not None and field.name != "file":
        field = await reader.next()

    if field is None:
        raise web.HTTPBadRequest(reason="Request must contain a 'file' field.")

    original_name: str = field.filename or "unknown"
    ext = Path(original_name).suffix.lower().lstrip(".")

    if not ext:
        raise web.HTTPBadRequest(reason="File has no extension.")

    # Validation is strictly case-insensitive because config["allowed_extensions"]
    # was converted to lowercase in main.py and `ext` is also converted to lowercase.
    if ext not in config["allowed_extensions"]:
        raise web.HTTPUnsupportedMediaType(
            reason=(
                f"Extension '.{ext}' is not permitted. "
                f"Allowed: {', '.join(sorted(config['allowed_extensions']))}"
            )
        )

    safe_stem = _sanitize_filename(Path(original_name).stem)
    unique_suffix = uuid.uuid4().hex[:8]
    dest_name = f"{safe_stem}_{unique_suffix}.{ext}"
    dest_path = Path(config["media_path"]) / dest_name

    total_bytes = 0
    max_bytes: int = config["max_bytes"]

    try:
        async with aiofiles.open(dest_path, "wb") as f:
            while True:
                chunk: bytes = await field.read_chunk(65536)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    await f.close()
                    dest_path.unlink(missing_ok=True)
                    raise web.HTTPRequestEntityTooLarge(
                        max_size=max_bytes,
                        actual_size=total_bytes,
                    )
                await f.write(chunk)
    except OSError as exc:
        logger.error("I/O error writing %s: %s", dest_path, exc)
        dest_path.unlink(missing_ok=True)
        raise web.HTTPInternalServerError(
            reason="Could not save file to disk."
        ) from exc

    client_ip = _get_client_ip(request)
    logger.info(
        "Upload OK: %s → %s (%d bytes from %s)",
        original_name,
        dest_name,
        total_bytes,
        client_ip,
    )

    if config["notify_on_upload"] and config["supervisor_token"]:
        global _notify_task
        _notify_files.append(dest_name)
        if _notify_task and not _notify_task.done():
            _notify_task.cancel()
        _notify_task = asyncio.create_task(
            _send_debounced_notification(
                config["supervisor_token"], config["notify_message"]
            )
        )

    return web.json_response(
        {"status": "ok", "filename": dest_name, "bytes": total_bytes}, status=201
    )


async def handle_list_photos(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)
    _check_csrf(request)

    media_path = Path(config["media_path"])
    allowed: frozenset[str] = config["allowed_extensions"]

    try:
        photos = []
        for f in media_path.iterdir():
            if f.is_file() and f.suffix.lower().lstrip(".") in allowed:
                st = f.stat()
                photos.append(
                    {
                        "name": f.name,
                        "size": st.st_size,
                        "modified": st.st_mtime,
                    }
                )
        photos.sort(key=lambda x: x["modified"], reverse=True)
    except OSError as exc:
        logger.error("Cannot list photos in %s: %s", media_path, exc)
        raise web.HTTPInternalServerError(
            reason="Could not read media directory."
        ) from exc

    return web.json_response({"photos": photos, "total": len(photos)})


async def handle_delete_photo(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)
    _check_csrf(request)

    raw_filename = request.match_info["filename"]
    filename = _sanitize_filename(raw_filename)
    media_root = Path(config["media_path"]).resolve()
    target = (media_root / filename).resolve()

    # Enhanced Path-traversal guard: target must strictly be inside media_root
    if not target.is_relative_to(media_root):
        logger.warning(
            "Path traversal blocked: %r resolved to %s", raw_filename, target
        )
        raise web.HTTPForbidden(reason="Path traversal attempt blocked.")

    if not target.exists():
        raise web.HTTPNotFound(reason=f"File '{filename}' not found.")

    if not target.is_file():
        raise web.HTTPBadRequest(reason=f"'{filename}' is not a regular file.")

    try:
        target.unlink()
    except OSError as exc:
        logger.error("Cannot delete %s: %s", target, exc)
        raise web.HTTPInternalServerError(reason="Could not delete file.") from exc

    # Cleanup orphaned thumbnail if exists (best-effort)
    try:
        thumb_path = media_root / ".thumbs" / f"{filename}.jpg"
        if thumb_path.exists():
            thumb_path.unlink()
    except OSError as exc:
        logger.warning("Could not delete thumbnail for %s: %s", filename, exc)

    client_ip = _get_client_ip(request)
    logger.info("Deleted: %s (requested by %s)", filename, client_ip)
    return web.json_response({"status": "deleted", "filename": filename})


def _generate_thumb_sync(src_path: Path, dst_path: Path) -> None:
    from PIL import Image, ImageOps

    with Image.open(src_path) as img:
        ImageOps.exif_transpose(img, in_place=True)
        img.thumbnail((256, 256), Image.Resampling.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(dst_path, format="JPEG", quality=80)


async def handle_get_thumb(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)

    raw_filename = request.match_info["filename"]
    filename = _sanitize_filename(raw_filename)
    media_root = Path(config["media_path"]).resolve()
    target = (media_root / filename).resolve()

    if not target.is_relative_to(media_root):
        raise web.HTTPForbidden(reason="Path traversal attempt blocked.")

    if not target.exists() or not target.is_file():
        raise web.HTTPNotFound(reason=f"File '{filename}' not found.")

    thumb_dir = media_root / ".thumbs"
    if not thumb_dir.exists():
        thumb_dir.mkdir(exist_ok=True)

    thumb_path = thumb_dir / f"{filename}.jpg"

    if not thumb_path.exists() or thumb_path.stat().st_mtime < target.stat().st_mtime:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                _executor, _generate_thumb_sync, target, thumb_path
            )
        except Exception as exc:
            logger.error("Thumbnail generation failed for %s: %s", target, exc)
            # Fallback to serving the original image
            return web.FileResponse(target)

    return web.FileResponse(thumb_path)


async def handle_get_media(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)

    raw_filename = request.match_info["filename"]
    filename = _sanitize_filename(raw_filename)
    media_root = Path(config["media_path"]).resolve()
    target = (media_root / filename).resolve()

    if not target.is_relative_to(media_root):
        logger.warning(
            "Path traversal blocked: %r resolved to %s", raw_filename, target
        )
        raise web.HTTPForbidden(reason="Path traversal attempt blocked.")

    if not target.exists() or not target.is_file():
        raise web.HTTPNotFound(reason=f"File '{filename}' not found.")

    return web.FileResponse(target)
