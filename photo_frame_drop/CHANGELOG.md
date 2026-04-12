# Changelog

All notable changes to Photo Frame Drop are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.0.35] - 2026-04-06
### Fixed
- Reverted the session cookie's `path`, `secure`, and `SameSite` modifications introduced during the security audit. Setting a dynamic `path` based on `X-Ingress-Path` caused total login failures under HA Ingress due to how Supervisor handles cookies across its internal proxy boundaries. Rolled back to the rock-solid base cookie structure to restore Ingress login functionality.

## [2.0.34] - 2026-04-06
### Fixed
- Fixed missing `handle_get_thumb` route mapping in the application router. The backend was fully generating the thumbnails but returning `404 Not Found` because the route `/thumb/{filename}` wasn't actually registered in the `aiohttp` web application instance.

## [2.0.33] - 2026-04-06
### Fixed
- Added a workaround for Home Assistant Ingress dropping session cookies: In addition to standard HTTP cookies, the authentication system now accepts the session token via a custom `Authorization: Bearer` header on API requests.

## [2.0.32] - 2026-04-06
### Fixed
- Fixed an issue where logging in via Home Assistant Ingress failed silently. Changed the session cookie's `SameSite` attribute from `Strict` to `Lax` to allow the cookie to be sent properly when the add-on is embedded inside the Home Assistant iframe interface.

## [2.0.32] - 2026-04-06
### Fixed
- Fixed missing `handle_get_thumb` route mapping in the application router. The backend was fully generating the thumbnails but returning `404 Not Found` because the route `/thumb/{filename}` wasn't actually registered in the `aiohttp` web application instance.

## [2.0.31] - 2026-04-06
### Security & Optimization
- **XSS Prevention**: Safely HTML-escaped the user-provided `login_description` string.
- **Cookie Scope**: Pinned the session cookie's `path` directive strictly to the addon's dynamic Ingress `base_path` rather than the HA root, reducing exposure and potential conflicts with other Home Assistant services.
- **Garbage Collection**: Fixed an issue where deleting a photo from the gallery left behind orphaned cache files in `.thumbs/`. Thumbnails are now properly removed alongside their source images (done as a best-effort, non-blocking operation).
- **Disk I/O Optimization**: Restructured the directory listing function to query the `stat()` metadata only once per file instead of twice, shaving off latency when loading galleries with thousands of images.
- **Path Validation**: Tightened `target_folder` validation in `run.sh` to fully reject any path-like structures containing slashes `/` or `\`.

## [2.0.30] - 2026-04-06
### Changed
- Reverted the login screen design to prominently feature the "Photo Frame Drop" title text below the logo, with the word "Drop" elegantly styled in blue (`#2563eb`), to better match the original aesthetic.
- Replaced the large square `logo_main.svg` on the login screen with the cleaner, plain logo (`logo_plain.svg`).
- Increased the size of the plain logo on the login screen and added a subtle white ambient glow effect to make it pop beautifully against the dark background.
- Fixed a bug where missing title elements on the login page crashed the translation script, rendering the "About" and "Language" buttons unresponsive.

## [2.0.28] - 2026-04-06
### Changed
- Removed the redundant HTML title text from the login screen, as the primary SVG logo already contains the full "Photo Frame Drop" typography.
- Increased the size of the logo on the login screen to better center the layout.
- Enlarged the plain logo (`logo_plain.svg`) in the top navigation bar of the gallery.
- Enhanced responsive design: The "Photo Frame Drop" text in the top navigation bar is now automatically hidden on small mobile screens to prevent layout overlap, leaving only the recognizable frame icon.

## [2.0.27] - 2026-04-06
### Added
- Complete branding overhaul! Replaced generic text emojis (`🖼️`, `📸`) with the custom SVG logos provided by the creator.
  - Added `logo_main.svg` to the login screen.
  - Added `logo_plain.svg` to the top-left navigation bar.
  - Added `logo_transparent.svg` as the header image inside the "About" dialog box.
  - Integrated the `Quicksand` Google Font to match the exact typography of the new logos.
  - Converted the main SVG to high-quality PNGs (`icon.png`, `logo.png`) for the Home Assistant Add-on Store display.
  - Drag-and-drop area now toggles between 📷 and 📸 emoji dynamically.

## [2.0.26] - 2026-04-06
### Fixed
- Fixed an issue where the "Delete" (X) button on photo cards was styled as raw text rather than an icon, resulting in layout misalignment and poor UI integration. Replaced the text 'X' with a clean, inline SVG trash can icon to match the application's aesthetic.

## [2.0.25] - 2026-04-06
### Added
- Expanded the "About" dialog to include a second button linking directly to the creator's GitHub profile (`@GwiezdnySzeryf`). Also fully integrated the texts of these new links into the dynamic EN/PL language translation system.

## [2.0.24] - 2026-04-06
### Added
- Added a loading spinner to the Lightbox gallery preview. When clicking a photo, a spinner will display while the high-resolution image is downloading from the server, and the old image is hidden entirely. The new image smoothly fades in once fully loaded, eliminating the "flashing" or glitchy visual delay of the previous photo sticking around.

## [2.0.23] - 2026-04-06
### Changed
- Re-architected the Lightbox photo preview mechanism to use the native HTML5 `<dialog>` element (just like the About window) instead of a custom CSS overlay toggle. This provides a much more accessible experience, natively blocks background scrolling, naturally dims the backdrop via the `::backdrop` pseudo-element, and inherits standard browser behavior (like closing on Escape key) without the need for manual event listeners.

## [2.0.22] - 2026-04-06
### Added
- Added an "About" dialog window accessible via the `?` button next to the language toggle. It contains brief information about the add-on and a link to the GitHub repository. It works across both the login and main pages and supports i18n translations.

## [2.0.21] - 2026-04-06
### Fixed
- Fixed a rendering bug where the text "Brak zdjęć" (No photos) would appear underneath the gallery even when photos were uploaded. Removed duplicated and improperly nested markup that was causing the grid CSS layout to fail hiding the text.

## [2.0.20] - 2026-04-06
### Fixed
- Fixed Lightbox styling and HTML injection.

## [2.0.19] - 2026-04-06
### Fixed
- Fixed an `unmatched ')'` SyntaxError in `server.py` on startup, which caused the add-on to fail to start and crash immediately upon launch.

## [2.0.18] - 2026-04-06
### Fixed
- Fixed an `unmatched ')'` SyntaxError in `server.py` on startup, which caused the add-on to fail to start and crash immediately upon launch.

## [2.0.17] - 2026-04-06
### Security & Optimization
- **Path Traversal Security**: Replaced string-based `.startswith()` checks with Python's safer `.is_relative_to()` to prevent edge-case directory escapes (e.g. escaping `/media/digital_frame` to `/media/digital_frame_secret`).
- **Docker Image Size**: Restructured the Dockerfile to use Alpine virtual build dependencies (`apk add --virtual`). Compilers (`build-base`, `libffi-dev`, etc.) are now completely removed after compiling Python wheels, significantly reducing the final Docker image size.
- **Translations**: Added Polish translation file (`translations/pl.yaml`) for the Home Assistant configuration UI natively.

## [2.0.16] - 2026-04-06
### Fixed
- Fixed bug causing an empty gallery and upload errors when using Home Assistant Ingress due to conflicting URL parsing in the Python backend.
- Added a 2-second debounce to the Home Assistant notification system so that uploading multiple photos at once (e.g. 50 files) sends only a single summary notification instead of spamming 50 separate alerts.

## [2.0.15] - 2026-04-06
### Fixed
- Fixed Home Assistant upload notifications not triggering (Error 401 Unauthorized in logs). Restored the `homeassistant_api: true` permission in `config.yaml` to allow the add-on's `SUPERVISOR_TOKEN` to successfully proxy requests to HA Core APIs like `persistent_notification.create`.

## [2.0.14] - 2026-04-05
### Added
- Added an optional `login_description` field to the add-on configuration. This text will be displayed on the login page just below the "Photo Frame Drop" title, allowing administrators to provide custom instructions.

## [2.0.13] - 2026-04-05
### Fixed
- Re-applied the backend thumbnail generation endpoint (`/thumb/{filename}`) and logic using `Pillow` which was accidentally rolled back during a previous merge, restoring actual images to the gallery thumbnails.

## [2.0.13] - 2026-04-05
### Added
- Added an optional `login_description` field to the add-on configuration. This text will be displayed on the login page just below the "Photo Frame Drop" title, allowing administrators to provide custom instructions (e.g., "Ask Tomek for the password").

## [2.0.12] - 2026-04-05
### Fixed
- Properly committed the HTML templates that implement the new EN/PL language toggle, the functional Sign out button, and the lightweight image thumbnails. A previous tool error prevented these UI changes from reaching the repository.

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
