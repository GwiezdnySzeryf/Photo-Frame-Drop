# OLD PAGE GO TO https://github.com/GwiezdnySzeryf/Gwiezdny-Szeryf-s-HA-Apps


## Photo Frame Drop

A **Home Assistant Add-on** that provides a password-protected, drag-and-drop
web interface for uploading photos directly into your HA `/media` folder —
ready to be picked up by any digital photo frame software pointed at that
directory.

---

## What It Does

| Feature | Detail |
|---------|--------|
| **Web UI via HA Ingress** | Accessible from the HA sidebar; no port-forwarding needed |
| **Drag & drop uploads** | Drop multiple photos at once; progress bar per file |
| **Gallery with delete** | Browse thumbnails and remove uploaded files from the same UI |
| **Password protection** | Session cookie with SHA-256 derived token with Brute Force protection |
| **File validation** | Extension allowlist + per-chunk size limit enforced server-side + filetype MIME validation |
| **HA notifications** | Optional persistent notification in HA after each upload |
| **Multi-arch** | Runs on `aarch64` and `amd64` |

---

## Architecture

```
Browser (any device, any location)
        │
        ▼  HTTPS via HA Ingress
aiohttp web server (port 8099, inside container)
        │
        ├──► /media/<target_folder>/   (HA media share, mapped read-write)
        │
        └──► http://supervisor/core/api/services/persistent_notification/create
             (optional — Supervisor REST API, only if notify_on_upload = true)
```

This is a standard HA Add-on: a Docker container managed by the HA Supervisor,
using `bashio` to read configuration and `s6-overlay` for process management.
It does not use WebSockets or polling — it is a stateless HTTP server.

---

## Installation

1. **Settings → Add-ons → Add-on Store**
2. Click ⋮ → **Repositories** → paste this URL → **Add**:
   ```
   https://github.com/GwiezdnySzeryf/Photo-Frame-Drop
   ```
3. Refresh the page, find **Photo Frame Drop**, click **Install**.
4. Go to the **Configuration** tab, set your password and target folder.
5. Click **Start**.

---

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `target_folder` | `str` | `digital_frame` | Subfolder inside `/media` to save photos |
| `password` | `str` | `changeme` | **Change this.** Web UI access password |
| `max_upload_mb` | `int` 1–500 | `50` | Max file size per upload in MB |
| `allowed_extensions` | `str` | `jpg,jpeg,png,gif,webp,bmp` | Comma-separated allowed extensions |
| `notify_on_upload` | `bool` | `false` | Send HA persistent notification on upload |
| `notify_message` | `str` | `New photo added to the frame!` | Notification body |
| `login_description` | `str` | `""` | Optional text displayed on the login page |

Full documentation is in [`photo_frame_drop/DOCS.md`](photo_frame_drop/DOCS.md)
and is also shown inside the HA add-on UI.

---

## Repository Structure

```
Photo-Frame-Drop/
├── repository.yaml                      # HA add-on repo manifest
├── README.md                            # This file
│
└── photo_frame_drop/                    # The add-on
    ├── config.yaml                      # Metadata, schema, ingress, watchdog
    ├── Dockerfile                       # Multi-arch, HA base Python image
    ├── requirements.txt                 # Pinned Python dependencies
    ├── DOCS.md                          # User docs (shown in HA UI)
    ├── CHANGELOG.md
    ├── icon.png                         # 256×256 add-on icon
    ├── logo.png                         # 256×100 add-on logo
    │
    ├── translations/
    │   └── en.yaml                      # Config option labels for HA UI
    │
    ├── rootfs/
    │   └── etc/services.d/photo_frame_drop/
    │       ├── run                      # s6 launcher: reads config, exports env
    │       └── finish                   # s6 exit handler
    │
    └── app/
        ├── main.py                      # Entrypoint, config validation, server runner
        ├── server.py                    # All HTTP route handlers
        ├── notifications.py             # HA Supervisor notification helper
        ├── templates/
        │   ├── login.html
        │   └── index.html               # Upload UI + gallery
        └── static/
            └── style.css
```

---

## License

MIT — see [LICENSE](LICENSE).
