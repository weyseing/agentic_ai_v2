#!/bin/sh

cd /app

# uvicorn
# uvicorn django_app.asgi:application --host 0.0.0.0 --port 5000 --reload &

# gunicorn
cp /app/nginx.conf /etc/nginx/conf.d &
gunicorn --bind 0.0.0.0:8000 --workers 16 --graceful-timeout=120 --timeout=120 --worker-class uvicorn.workers.UvicornWorker django_app.asgi:application & 
nginx -g "daemon off;" -c /etc/nginx/conf.d/nginx.conf             
