#!/bin/bash
set -e

echo "Running Database Migrations..."
# Run alembic migrations
alembic upgrade head


if [ -n "$1" ]; then
    exec "$@"
fi
