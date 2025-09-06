#!/bin/bash

export PYTHONPATH="/app:${PYTHONPATH}"

case "$1" in
    "ranker")
        cd /app/ranker && python api.py
        ;;
    "ranker_worker")
        cd /app/ranker && celery -A celery_app worker --loglevel=info --concurrency=4 -Ofair -Q ranker
        ;;
    *)
        exec "$@"
        ;;
esac
