#!/usr/bin/env bash
#
# IEAP - Entry point script for Docker container
#

set -e

# Default values
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
WORKERS=${WORKERS:-4}

# Wait for database to be ready
wait_for_db() {
    echo "Waiting for database..."
    while ! nc -z "${POSTGRES_HOST:-postgres}" "${POSTGRES_PORT:-5432}"; do
        sleep 1
    done
    echo "Database is ready!"
}

# Wait for Redis to be ready
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! nc -z "${REDIS_HOST:-redis}" "${REDIS_PORT:-6379}"; do
        sleep 1
    done
    echo "Redis is ready!"
}

# Run database migrations
run_migrations() {
    echo "Running database migrations..."
    alembic upgrade head
    echo "Migrations complete!"
}

# Start the API server
start_api() {
    echo "Starting API server..."
    exec uvicorn api.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --workers "$WORKERS" \
        --access-log \
        --proxy-headers
}

# Start Celery worker
start_worker() {
    echo "Starting Celery worker..."
    exec celery -A cache.celery_app worker \
        --loglevel=info \
        --concurrency="${CELERY_CONCURRENCY:-4}" \
        --queues="${CELERY_QUEUES:-default,ml_tasks,pipeline_tasks,webhooks}"
}

# Start Celery beat scheduler
start_beat() {
    echo "Starting Celery beat..."
    exec celery -A cache.celery_app beat \
        --loglevel=info \
        --scheduler=celery.beat.DatabaseScheduler
}

# Start Flower monitoring
start_flower() {
    echo "Starting Flower..."
    exec celery -A cache.celery_app flower \
        --port="${FLOWER_PORT:-5555}" \
        --url_prefix=flower
}

# Development server with hot reload
start_dev() {
    echo "Starting development server with hot reload..."
    exec uvicorn api.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --reload-dir /app \
        --access-log
}

# Main entrypoint
main() {
    case "${1:-api}" in
        api)
            wait_for_db
            wait_for_redis
            run_migrations
            start_api
            ;;
        worker)
            wait_for_db
            wait_for_redis
            start_worker
            ;;
        beat)
            wait_for_db
            wait_for_redis
            start_beat
            ;;
        flower)
            wait_for_redis
            start_flower
            ;;
        dev)
            wait_for_db
            wait_for_redis
            run_migrations
            start_dev
            ;;
        migrate)
            wait_for_db
            run_migrations
            ;;
        shell)
            exec /bin/bash
            ;;
        *)
            exec "$@"
            ;;
    esac
}

main "$@"
