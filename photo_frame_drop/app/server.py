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

from __future__ import annotations

import hashlib
import logging
import mimetypes
import re
import uuid
from pathlib import Path
from typing import Any

import aiofiles
from aiohttp import web

from notifications import send_ha_notification

logger = logging.getLogger("photo_frame_drop.server")

# Only allow filenames made of safe characters
_UNSAFE_CHARS = re.compile(r"[^\w\-. ]")

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


# ---------------------------------------------------------------------------- #
# Helpers                                                                       #
# ---------------------------------------------------------------------------- #


def _sanitize_filename(name: str) -> str:
    """Strip directory components and replace unsafe characters."""
    name = Path(name).name  # removes any directory prefix
    name = _UNSAFE_CHARS.sub("_", name)
    return name.strip() or "upload"


def _session_value(password: str) -> str:
    """Derive a deterministic session token from the configured password."""
    return hashlib.sha256(f"pfd:{password}".encode()).hexdigest()


def _is_authenticated(config: dict[str, Any], request: web.Request) -> bool:
    return request.cookies.get("pfd_session") == _session_value(config["password"])


def _require_auth(config: dict[str, Any], request: web.Request) -> None:
    """Raise 401 if the request is not authenticated."""
    if not _is_authenticated(config, request):
        raise web.HTTPUnauthorized(reason="Authentication required")


# ---------------------------------------------------------------------------- #
# App factory                                                                   #
# ---------------------------------------------------------------------------- #


def create_app(config: dict[str, Any]) -> web.Application:
    """Create and configure the aiohttp Application."""
    # max request size = configured limit + 64 KB headroom for multipart headers
    app = web.Application(client_max_size=config["max_bytes"] + 65536)
    app["config"] = config

    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_index)
    app.router.add_post("/login", handle_login)
    app.router.add_post("/logout", handle_logout)
    app.router.add_post("/upload", handle_upload)
    app.router.add_get("/photos", handle_list_photos)
    app.router.add_delete("/photos/{filename}", handle_delete_photo)

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
    """Watchdog endpoint — must stay fast and side-effect-free."""
    return web.json_response({"status": "ok"})


async def handle_index(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    base_path = _get_base_path(request)

    if not _is_authenticated(config, request):
        text = (TEMPLATES_DIR / "login.html").read_text()
        text = text.replace('href="/static/', f'href="{base_path}/static/')
        text = text.replace('action="/login"', f'action="{base_path}/login"')
        return web.Response(text=text, content_type="text/html")

    text = (TEMPLATES_DIR / "index.html").read_text()
    text = text.replace('href="/static/', f'href="{base_path}/static/')
    text = text.replace('action="/logout"', f'action="{base_path}/logout"')
    text = text.replace('"/upload"', f'"{base_path}/upload"')
    text = text.replace('"/photos"', f'"{base_path}/photos"')
    text = text.replace("`/photos/", f"`{base_path}/photos/")
    return web.Response(text=text, content_type="text/html")


async def handle_login(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    base_path = _get_base_path(request)
    data = await request.post()
    entered: str = data.get("password", "")

    if entered == config["password"]:
        response = web.HTTPFound(f"{base_path}/")
        response.set_cookie(
            "pfd_session",
            _session_value(config["password"]),
            httponly=True,
            samesite="Strict",
            max_age=7 * 24 * 3600,  # 1 week
        )
        logger.info("Successful login from %s", request.remote)
        return response

    logger.warning("Failed login attempt from %s", request.remote)
    # Redirect back to login page with an error flag in the query string
    return web.HTTPFound(f"{base_path}/?error=wrong_password")


async def handle_logout(request: web.Request) -> web.Response:
    base_path = _get_base_path(request)
    response = web.HTTPFound(f"{base_path}/")
    response.del_cookie("pfd_session")
    return response


async def handle_upload(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)

    reader = await request.multipart()

    # Drain fields until we hit the file field
    field = await reader.next()
    while field is not None and field.name != "file":
        field = await reader.next()

    if field is None:
        raise web.HTTPBadRequest(reason="Request must contain a 'file' field.")

    original_name: str = field.filename or "unknown"
    ext = Path(original_name).suffix.lower().lstrip(".")

    if not ext:
        raise web.HTTPBadRequest(reason="File has no extension.")

    if ext not in config["allowed_extensions"]:
        raise web.HTTPUnsupportedMediaType(
            reason=(
                f"Extension '.{ext}' is not permitted. "
                f"Allowed: {', '.join(sorted(config['allowed_extensions']))}"
            )
        )

    # Build a unique destination filename to avoid silent overwrites
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
                    # Clean up the partial file before raising
                    await f.close()  # type: ignore[attr-defined]
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

    logger.info(
        "Upload OK: %s → %s (%d bytes from %s)",
        original_name,
        dest_name,
        total_bytes,
        request.remote,
    )

    if config["notify_on_upload"] and config["supervisor_token"]:
        await send_ha_notification(
            token=config["supervisor_token"],
            message=f"{config['notify_message']} [{dest_name}]",
        )

    return web.json_response(
        {"status": "ok", "filename": dest_name, "bytes": total_bytes},
        status=201,
    )


async def handle_list_photos(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)

    media_path = Path(config["media_path"])
    allowed: frozenset[str] = config["allowed_extensions"]

    try:
        photos = sorted(
            [
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                }
                for f in media_path.iterdir()
                if f.is_file() and f.suffix.lower().lstrip(".") in allowed
            ],
            key=lambda x: x["modified"],
            reverse=True,
        )
    except OSError as exc:
        logger.error("Cannot list photos in %s: %s", media_path, exc)
        raise web.HTTPInternalServerError(
            reason="Could not read media directory."
        ) from exc

    return web.json_response({"photos": photos, "total": len(photos)})


async def handle_delete_photo(request: web.Request) -> web.Response:
    config: dict = request.app["config"]
    _require_auth(config, request)

    raw_filename = request.match_info["filename"]
    filename = _sanitize_filename(raw_filename)
    media_root = Path(config["media_path"]).resolve()
    target = (media_root / filename).resolve()

    # Path-traversal guard: resolved path must be inside media_root
    try:
        target.relative_to(media_root)
    except ValueError:
        logger.warning(
            "Path traversal blocked: %r resolved to %s (outside %s)",
            raw_filename,
            target,
            media_root,
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

    logger.info("Deleted: %s (requested by %s)", filename, request.remote)
    return web.json_response({"status": "deleted", "filename": filename})
