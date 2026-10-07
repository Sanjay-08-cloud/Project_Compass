#!/bin/bash
set -e

echo "Starting Project Compass Service..."

# Wait for PostgreSQL if configured
if [ "$USE_POSTGRESQL" = "True" ] || [ "$USE_POSTGRESQL" = "true" ]; then
    echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
    while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
        sleep 0.5
    done
    echo "PostgreSQL is ready!"
fi

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static assets..."
python manage.py collectstatic --noinput || true

# Seed demonstration data if needed
echo "Seeding demo accounts and projects..."
python manage.py seed_phase1 || true
python manage.py seed_phase2_docs || true
python manage.py rebuild_indexes || true

echo "Project Compass initialized successfully!"

# Execute container command (runserver, gunicorn, or celery)
exec "$@"
