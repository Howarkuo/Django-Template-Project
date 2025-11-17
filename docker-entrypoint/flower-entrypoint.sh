#!/bin/sh

cd /ainsight_backend
celery -A config flower --port=5555 --basic_auth=$CELERY_FLOWER_USER:$CELERY_FLOWER_PASSWORD

exec "$@"
