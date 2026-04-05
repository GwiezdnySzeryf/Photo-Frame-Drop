#!/usr/bin/with-contenv bashio

echo "Uruchamianie serwera Photo Frame Drop..."

# Pobranie konfiguracji
export ACCESS_KEY=$(bashio::config 'access_key')
export UPLOAD_FOLDER=$(bashio::config 'upload_folder')
export NOTIFY_ON_UPLOAD=$(bashio::config 'notify_on_upload')

# Zapewnienie, że folder istnieje
mkdir -p "/media/${UPLOAD_FOLDER}"

# Uruchomienie aplikacji FastAPI
cd /app
exec uvicorn main:app --host 0.0.0.0 --port 8000
