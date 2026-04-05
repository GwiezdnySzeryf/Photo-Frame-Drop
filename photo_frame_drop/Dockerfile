ARG BUILD_FROM=ghcr.io/hassio-addons/base-python:18.0.0
FROM $BUILD_FROM

# Install system dependencies for python-magic
RUN apk add --no-cache libmagic file

# Copy requirements and install Python dependencies
COPY app/requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application files
COPY run.sh /
COPY app /app

RUN chmod a+x /run.sh

WORKDIR /app

CMD [ "/run.sh" ]
