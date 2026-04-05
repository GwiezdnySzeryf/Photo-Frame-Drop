ARG BUILD_FROM=ghcr.io/hassio-addons/base-python:13.1.2
FROM $BUILD_FROM

# Install requirements
COPY app/requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# Copy root filesystem
COPY run.sh /
COPY app /app

RUN chmod a+x /run.sh

WORKDIR /app

CMD [ "/run.sh" ]
