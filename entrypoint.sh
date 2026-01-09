#!/bin/sh
set -e

echo "Starting AI service initialization..."

# Run database migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Running Alembic migrations..."
  alembic upgrade head
  echo "Migrations completed."
fi

# Start the application
echo "Starting uvicorn server..."
exec uvicorn src.main:app --host 0.0.0.0 --port ${SERVICE_PORT:-8000}

