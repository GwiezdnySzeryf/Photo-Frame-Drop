# Changelog

All notable changes to Photo Frame Drop are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

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
