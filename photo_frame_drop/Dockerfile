ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    libmagic \
    file

# Copy requirements and install Python dependencies
COPY app/requirements.txt /tmp/
RUN pip install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Copy application files
COPY run.sh /
COPY app /app

RUN chmod a+x /run.sh

WORKDIR /app

CMD [ "/run.sh" ]
