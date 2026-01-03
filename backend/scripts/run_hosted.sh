#!/bin/bash
set -e

echo "Running database migrations..."
python -m alembic -c src/neurocache/alembic.ini upgrade head

echo "Starting production server..."
python -m uvicorn neurocache.app:app --host 0.0.0.0 --port ${UVICORN_PORT:-8000}
