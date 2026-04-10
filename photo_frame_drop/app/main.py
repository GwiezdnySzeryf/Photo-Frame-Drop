"""Photo Frame Drop — Home Assistant Add-on entry point.

Reads configuration from environment variables (populated by run.sh via bashio),
validates them, then starts the aiohttp web server.
"""

import asyncio
import logging
import os
import sys

from server import create_app

# ---------------------------------------------------------------------------- #
# Logging setup — stdout so the HA Supervisor captures it                      #
# ---------------------------------------------------------------------------- #

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("photo_frame_drop")


# ---------------------------------------------------------------------------- #
# Configuration loading                                                         #
# ---------------------------------------------------------------------------- #


def load_config() -> dict:
    """Load and validate all configuration from environment variables.

    All variables are set by rootfs/etc/services.d/photo_frame_drop/run
    via bashio reading the add-on config.yaml options.

    Raises SystemExit on missing or invalid values.
    """
    required_vars = [
        "PHOTO_FRAME_MEDIA_PATH",
        "PHOTO_FRAME_PASSWORD",
        "PHOTO_FRAME_MAX_MB",
        "PHOTO_FRAME_EXTENSIONS",
    ]

    missing = [v for v in required_vars if not os.environ.get(v)]
    if missing:
        for var in missing:
            logger.error("Missing required environment variable: %s", var)
        sys.exit(1)

    # Parse and normalise allowed extensions to a frozenset of lowercase strings
    # without leading dots: {"jpg", "jpeg", "png", ...}
    raw_ext = os.environ["PHOTO_FRAME_EXTENSIONS"]
    allowed_extensions: frozenset[str] = frozenset(
        ext.strip().lower().lstrip(".") for ext in raw_ext.split(",") if ext.strip()
    )
    if not allowed_extensions:
        logger.error(
            "PHOTO_FRAME_EXTENSIONS is set but contains no valid extensions: %r",
            raw_ext,
        )
        sys.exit(1)

    try:
        max_mb = int(os.environ["PHOTO_FRAME_MAX_MB"])
        if max_mb < 1:
            raise ValueError("must be >= 1")
    except ValueError as exc:
        logger.error("Invalid PHOTO_FRAME_MAX_MB value: %s", exc)
        sys.exit(1)

    port = int(os.environ.get("PHOTO_FRAME_PORT", "8099"))

    return {
        "media_path": os.environ["PHOTO_FRAME_MEDIA_PATH"],
        "password": os.environ["PHOTO_FRAME_PASSWORD"],
        "max_bytes": max_mb * 1024 * 1024,
        "allowed_extensions": allowed_extensions,
        "notify_on_upload": os.environ.get("PHOTO_FRAME_NOTIFY", "false").lower()
        == "true",
        "notify_message": os.environ.get(
            "PHOTO_FRAME_NOTIFY_MSG", "New photo uploaded!"
        ),
        "notify_on_failed_login": os.environ.get(
            "PHOTO_FRAME_NOTIFY_FAILED_LOGIN", "true"
        ).lower()
        == "true",
        "login_description": os.environ.get("PHOTO_FRAME_LOGIN_DESC", ""),
        "supervisor_token": os.environ.get("PHOTO_FRAME_SUPERVISOR_TOKEN", ""),
        "port": port,
    }


# ---------------------------------------------------------------------------- #
# Main                                                                          #
# ---------------------------------------------------------------------------- #


async def main() -> None:
    config = load_config()

    logger.info("Starting Photo Frame Drop")
    logger.info("  Port            : %d", config["port"])
    logger.info("  Media path      : %s", config["media_path"])
    logger.info("  Max upload size : %d MB", config["max_bytes"] // (1024 * 1024))
    logger.info(
        "  Allowed exts    : %s", ", ".join(sorted(config["allowed_extensions"]))
    )
    logger.info(
        "  Notifications   : %s",
        "enabled" if config["notify_on_upload"] else "disabled",
    )

    from aiohttp import web

    app = create_app(config)
    runner = web.AppRunner(app, access_log=logging.getLogger("photo_frame_drop.access"))
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config["port"])
    await site.start()

    logger.info("Server ready at http://0.0.0.0:%d", config["port"])

    try:
        # Block forever — s6 handles restarts and shutdown signals
        await asyncio.Event().wait()
    finally:
        logger.info("Shutting down...")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
