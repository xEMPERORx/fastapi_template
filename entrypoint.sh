#!/bin/bash
set -e

echo "Running Database Migrations..."
# Run alembic migrations
alembic upgrade head

# Bootstrap the first superuser on a fresh database (see the `seed-admin`
# skill / app/cli/seed.py's own docstring for why is_superuser can only ever
# be set here, never through a request schema). Only runs non-interactively
# when all three env vars are set — otherwise app/cli/seed.py falls back to
# interactive prompts, which would hang a container with no attached stdin.
# Safe to run on every startup: seed.py checks exists_by_username() first and
# no-ops once the user already exists, so this isn't a one-time-only step.
if [ -n "$SEED_ADMIN_USERNAME" ] && [ -n "$SEED_ADMIN_EMAIL" ] && [ -n "$SEED_ADMIN_PASSWORD" ]; then
    echo "Seeding superuser '$SEED_ADMIN_USERNAME'..."
    python -m app.cli.seed
else
    echo "SEED_ADMIN_USERNAME/EMAIL/PASSWORD not set in .env — skipping superuser seed."
    echo "Set them in .env and restart, or run 'docker compose exec api python -m app.cli.seed' manually."
fi

if [ -n "$1" ]; then
    exec "$@"
fi
