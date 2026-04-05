"""Home Assistant Supervisor — notification helper.

Sends a persistent notification via the HA Core REST API, proxied through
the Supervisor. Requires ``hassio_api: true`` in config.yaml.

The Supervisor injects the ``SUPERVISOR_TOKEN`` environment variable; this
token is used as a Bearer token for requests to http://supervisor/...
"""

from __future__ import annotations

import logging
from typing import Optional

import aiohttp

logger = logging.getLogger("photo_frame_drop.notifications")

# Supervisor-proxied HA Core REST endpoint
_NOTIFY_URL = "http://supervisor/core/api/services/persistent_notification/create"

# Reuse a single connector across calls for the lifetime of the process
_connector: Optional[aiohttp.TCPConnector] = None


def _get_connector() -> aiohttp.TCPConnector:
    global _connector
    if _connector is None or _connector.closed:
        _connector = aiohttp.TCPConnector(limit=4)
    return _connector


async def send_ha_notification(
    token: str,
    message: str,
    title: str = "Photo Frame Drop",
    notification_id: str = "photo_frame_drop_upload",
) -> None:
    """Send a persistent notification to Home Assistant.

    This call is best-effort: failures are logged as warnings but never
    re-raised so they cannot disrupt the upload response.

    Args:
        token: The Supervisor token (value of $SUPERVISOR_TOKEN).
        message: Notification body text.
        title: Notification title shown in the HA UI.
        notification_id: Stable ID; subsequent calls replace the same card.
    """
    if not token:
        logger.warning(
            "Cannot send HA notification: SUPERVISOR_TOKEN is empty. "
            "Make sure 'hassio_api: true' is set in config.yaml."
        )
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": message,
        "title": title,
        "notification_id": notification_id,
    }

    try:
        async with aiohttp.ClientSession(
            connector=_get_connector(),
            connector_owner=False,
        ) as session:
            async with session.post(
                _NOTIFY_URL,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status not in (200, 201):
                    body = await resp.text()
                    logger.warning(
                        "HA notification API returned HTTP %d: %s",
                        resp.status,
                        body[:200],
                    )
                else:
                    logger.info("HA notification sent: %s", message)
    except aiohttp.ClientError as exc:
        logger.warning("HA notification failed (network error): %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("HA notification failed (unexpected): %s", exc)
