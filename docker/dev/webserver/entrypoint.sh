#!/bin/bash

export PYTHONPATH="/app:${PYTHONPATH}"

case "$1" in
    "web")
        cd /app/webserver/search && uvicorn search.asgi:application --host 0.0.0.0 --port 8000
        ;;
    "webserver_worker")
        cd /app/webserver/search && celery -A search worker --concurrency=8 -l INFO
        ;;
    *)
        exec "$@"
        ;;
esac