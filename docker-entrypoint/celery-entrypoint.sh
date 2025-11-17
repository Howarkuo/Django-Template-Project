#!/bin/sh

celery -A config worker -l info -E

exec "$@"
