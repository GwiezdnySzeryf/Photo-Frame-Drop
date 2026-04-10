ARG BUILD_FROM
FROM $BUILD_FROM

# Install OS-level dependencies needed by Pillow and aiohttp
RUN apk add --no-cache \
    python3 \
    py3-pip \
    libjpeg-turbo \
    libpng \
    libwebp \
    zlib

WORKDIR /app

# Copy and install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN apk add --no-cache --virtual .build-deps \
    build-base \
    libffi-dev \
    libjpeg-turbo-dev \
    libpng-dev \
    libwebp-dev \
    zlib-dev \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt \
    && apk del .build-deps

# Copy s6-overlay service scripts
COPY rootfs/ /

RUN chmod a+x \
    /etc/services.d/photo_frame_drop/run \
    /etc/services.d/photo_frame_drop/finish

# Copy application source
COPY app/ /app/

ARG BUILD_VERSION
LABEL \
    io.hass.version="${BUILD_VERSION}" \
    io.hass.type="addon" \
    io.hass.arch="aarch64|amd64"
