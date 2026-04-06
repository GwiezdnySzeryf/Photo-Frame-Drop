# Changelog

All notable changes to Photo Frame Drop are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.11] - 2026-04-05
### Added
- Added multi-language support! There is now an EN/PL toggle switch next to the Sign out button. It remembers your choice in local storage.
- The server now generates lightweight `256x256` thumbnails on-the-fly (cached in `.thumbs/`) instead of delivering the entire multi-megabyte image over the network just to render the tiny preview square. Greatly improves gallery load times.

## [2.0.10] - 2026-04-05
### Fixed
- Fixed the "Sign out" button completely. Ingress pathing rules caused the `fetch("/logout")` Javascript call to break out of the addon and crash to a generic Cloudflare 524 Timeout error because it lacked the `X-Ingress-Path` prefix.

## [2.0.9] - 2026-04-05
### Fixed
- Fixed massive, unconstrained image previews when accessed via Home Assistant Ingress. Home Assistant heavily caches static files, causing the browser to load an older version of the CSS file without the new thumbnail constraints. Added a version query parameter (`?v=2.0.9`) to the `style.css` stylesheet link in Python backend to definitively bust the browser cache.

## [2.0.8] - 2026-04-05
### Fixed
- Fixed broken layout and raw template string output (`${escapeHtml(photo.name)}`) in the photo gallery caused by escaped backslashes in JavaScript template literals.

## [2.0.7] - 2026-04-05
### Added
- Image previews in the gallery! Instead of a generic document icon, the gallery now shows a square thumbnail preview of each uploaded photo. 

## [2.0.6] - 2026-04-05
### Security
- Fixed multiple vulnerabilities reported in security audit:
  - **Deterministic sessions**: Add-on now generates a random secure secret on startup (`secrets.token_urlsafe(32)`) to mix into the session hash, preventing session token prediction.
  - **Rate limiting**: Added in-memory rate limiting to the `/login` route (blocks IP after 5 failed attempts within 5 minutes) to protect against brute-force attacks.
  - **Secure Cookie**: The `pfd_session` cookie now properly uses `secure=True` if the request was made over HTTPS (checked via `X-Forwarded-Proto` or scheme).
  - **CSRF Protection**: Added strict `X-Requested-With: XMLHttpRequest` header checks for all API endpoints (`/upload`, `/photos`, `/logout`) to prevent Cross-Site Request Forgery.
  - **Logging**: The rate limiter and login functions now properly extract the real client IP using the `X-Forwarded-For` header instead of relying purely on the internal proxy IP.

## [2.0.5] - 2026-04-05
### Changed
- Re-exposed `8099/tcp` in the `ports` configuration to allow direct, independent network access (e.g. for reverse proxy or external sharing) while still maintaining the internal HA Ingress functionality.

## [2.0.4] - 2026-04-05
### Fixed
- Fixed broken UI and `524 A timeout occurred` Cloudflare error when using HA Ingress. Ingress accesses the app through a dynamic path (`/api/hassio_ingress/xxx`), causing absolute HTML paths to route to the main HA domain and break out of the addon context. Handled `X-Ingress-Path` internally to serve properly routed frontend assets and redirects.

## [2.0.3] - 2026-04-05
### Fixed
- Removed deprecated 32-bit architectures (`armhf`, `armv7`, `i386`) from `config.yaml`, `build.yaml`, and `Dockerfile` labels to clear Supervisor warnings. Home Assistant Add-ons are moving towards 64-bit only (`aarch64`, `amd64`).

## [2.0.2] - 2026-04-05
### Fixed
- Fixed build error on ARM platforms where Supervisor would fall back to a generic Alpine image without Python. Added `build.yaml` to strictly define the `base-python` image for all architectures.
- Added safety-net Python installation in Dockerfile in case a bare image is ever injected.

## [2.0.1] - 2026-04-05
### Fixed
- Fixed `pip: not found` error during add-on build by switching to `pip3` in the Dockerfile.

## [2.0.0] — 2024-04-05

### Breaking changes

- **Python web server replaced**: Flask (synchronous) replaced with `aiohttp`
  (async). Concurrent uploads no longer block each other.
- **Service entrypoint restructured**: `run.sh` replaced with a proper s6-overlay
  service under `rootfs/etc/services.d/`. Behaviour is identical from the user's
  perspective.
- **Filenames are now unique**: uploaded files get a random 8-character suffix
  appended (e.g. `photo_a3f9c12b.jpg`) to prevent silent overwrites. Old files
  in `/media` are not affected.

### Added

- `watchdog` field in `config.yaml` — Supervisor now auto-restarts the add-on
  if the `/health` endpoint stops responding.
- `ingress: true` — add-on is accessible via the HA sidebar with no port
  forwarding required.
- `translations/en.yaml` — configuration option labels are now human-readable
  in the HA UI instead of showing raw key names.
- Path-traversal protection on file delete: resolved paths are validated against
  the media root before deletion.
- Per-chunk upload size enforcement: oversized uploads are rejected mid-stream
  and partial files are cleaned up.
- `notify_on_upload` option: sends a HA persistent notification via the
  Supervisor REST API after each successful upload.
- Sign out button in the gallery UI.
- Upload progress bar per file.
- Startup warning in logs if the default password `changeme` is still in use.
- Input validation in `run.sh`: rejects `target_folder` values containing `..`
  or starting with `/`.
- `finish` service script: logs non-zero exit codes instead of silent failure.

### Fixed

- Session cookie is now `HttpOnly` and `SameSite=Strict`.
- Session value is a SHA-256 hash of the password, not the plaintext password.
- `allowed_extensions` is now enforced server-side, not just in the file picker.
- `max_upload_mb` is enforced per-chunk during streaming, not after full receipt.

### Changed

- Multi-arch support: `Dockerfile` uses `ARG BUILD_FROM` against the official
  HA base Python image, supporting `aarch64`, `amd64`, `armhf`, `armv7`, `i386`.
- All Python dependencies pinned to exact versions in `requirements.txt`.

---

## [1.x.x] — Initial releases

Original Flask-based implementation.
