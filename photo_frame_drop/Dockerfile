ARG BUILD_FROM=ghcr.io/home-assistant/base-python:3.12-alpine3.19
FROM $BUILD_FROM

# Install OS-level dependencies needed by Pillow and aiohttp
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    libjpeg-turbo-dev \
    libpng-dev \
    libwebp-dev \
    zlib-dev

WORKDIR /app

# Copy and install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy s6-overlay service scripts
COPY rootfs/ /

RUN chmod a+x \
    /etc/services.d/photo_frame_drop/run \
    /etc/services.d/photo_frame_drop/finish

# Copy application source
COPY app/ /app/

LABEL \
    io.hass.version="2.0.0" \
    io.hass.type="addon" \
    io.hass.arch="aarch64|amd64|armhf|armv7|i386"
