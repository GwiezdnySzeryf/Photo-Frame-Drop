# Photo Frame Drop — Documentation

## What It Does

Photo Frame Drop is a Home Assistant Add-on that provides a password-protected,
drag-and-drop web interface for uploading photos directly into your HA `/media`
folder. It is designed to work alongside any digital photo frame software
(Pi3D PictureFrame, kiosk browser, slideshow app) that monitors a local folder.

---

## How It Connects to Home Assistant

This add-on runs as a Docker container managed by the HA Supervisor.

```
Browser (any device, any location)
    │
    ▼
HA Ingress (no port-forwarding required)
    │
    ▼  HTTP  
aiohttp web server  ─────────────────────►  /media/<target_folder>/
    │
    │  (optional, if notify_on_upload = true)
    ▼
Supervisor REST API → persistent_notification/create
```

- **Storage**: photos land directly in HA's `/media` share, mapped read-write.
- **Auth**: HA Ingress session + a separate add-on password cookie.
- **Notifications**: sent via `http://supervisor/core/api/...` using the
  `$SUPERVISOR_TOKEN` injected by the Supervisor. Requires `hassio_api: true`
  (already set in `config.yaml`).
- **No polling, no WebSocket**: the add-on is a stateless HTTP server; all
  state lives in the filesystem.

---

## Installation

1. In Home Assistant go to **Settings → Add-ons → Add-on Store**.
2. Click ⋮ (top right) → **Repositories**.
3. Paste `https://github.com/GwiezdnySzeryf/Photo-Frame-Drop` and click **Add**.
4. Close the dialog and refresh the page.
5. Find **Photo Frame Drop** and click **Install**.

---

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `target_folder` | string | `digital_frame` | Subfolder inside `/media` where photos are saved |
| `password` | string | `changeme` | Web UI access password — **change before use** |
| `max_upload_mb` | int 1–500 | `50` | Maximum allowed file size per upload |
| `allowed_extensions` | string | `jpg,jpeg,png,gif,webp,bmp` | Comma-separated permitted extensions |
| `notify_on_upload` | bool | `false` | Send HA notification after each upload |
| `notify_message` | string | `New photo added to the frame!` | Notification body text |

### Important: change the default password

The default password is `changeme`. Change it in the **Configuration** tab before
starting the add-on. If you forget, the add-on will log a warning on every start.

---

## Usage

1. Configure and **Start** the add-on.
2. Open the UI via the **Photo Frame Drop** entry in the sidebar (or
   **Open Web UI** on the add-on page).
3. Enter your password.
4. Drag photos onto the upload zone, or click to browse.
5. Uploaded photos appear immediately in `/media/<target_folder>/`.

Point your frame software at the same path.

---

## Accessing from Outside Your Local Network

The add-on uses **HA Ingress** by default — no extra port forwarding needed.
If your HA instance is reachable externally (via Nabu Casa / Home Assistant
Cloud, Nginx Proxy Manager, or Cloudflare Tunnel), the add-on UI is
automatically accessible at the same address.

> **Do not expose port 8099 directly** to the internet. Use HA Ingress or
> a TLS-terminating reverse proxy instead.

---

## Troubleshooting

### Photos are not appearing on the frame

- Confirm `target_folder` in add-on config matches the folder your frame
  software monitors.
- Check **Logs** tab: the add-on logs the full destination path on startup.
- Verify the `/media` share exists and is writable in HA
  (**Settings → System → Storage**).

### Upload fails immediately

- Check that the file extension is in `allowed_extensions`.
- Check that the file is under `max_upload_mb`.
- Check **Logs** for the specific rejection reason.

### "Authentication required" after uploading from a different device

- The session cookie is device-specific. Each new browser/device needs to
  log in once.
- Cookie lifetime is 7 days.

### Notifications are not appearing in HA

- Confirm `notify_on_upload` is `true` and the add-on has been restarted
  after changing the setting.
- Check Logs for `HA notification sent` or any warning lines.
- Persistent notifications appear in HA under the 🔔 bell icon.

### Add-on fails to start

1. Open the **Logs** tab.
2. Look for lines starting with `[FATAL]` — these explain the exact reason.
3. Common causes:
   - `target_folder` contains `..` or starts with `/`
   - The `/media` share is not enabled in your HA installation

---

## Limitations

- Single shared password — no per-user accounts.
- No thumbnail preview in the gallery (filenames and file sizes only).
- Files deleted directly from the filesystem are not reflected in the gallery
  until the page is refreshed.
- The add-on does **not** display photos — it only manages uploads.
