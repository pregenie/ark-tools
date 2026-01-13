#!/bin/bash
set -e

echo "🚀 Starting ARK-TOOLS API Server"
echo "Environment: ${FLASK_ENV:-production}"
echo "Debug: ${FLASK_DEBUG:-false}"

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
python -c "
import time
import sys
from ark_tools.database.base import db_manager

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        status = db_manager.check_connection()
        if status['connected']:
            print('✅ Database connection established')
            break
    except Exception as e:
        print(f'⏳ Database not ready yet (attempt {retry_count + 1}/{max_retries}): {e}')
    
    retry_count += 1
    time.sleep(2)
else:
    print('❌ Failed to connect to database after maximum retries')
    sys.exit(1)
"

# Initialize database tables if needed
echo "🔧 Initializing database..."
python -c "
from ark_tools.database.base import db_manager
try:
    db_manager.create_tables()
    print('✅ Database tables initialized')
except Exception as e:
    print(f'⚠️  Database initialization warning: {e}')
"

# Start the application
echo "🌟 Starting ARK-TOOLS API on port 5000..."

if [ "${FLASK_ENV}" = "development" ] || [ "${FLASK_DEBUG}" = "true" ]; then
    echo "🔧 Running in development mode"
    exec python -m flask run --host=0.0.0.0 --port=5000
else
    echo "🏭 Running in production mode with Gunicorn"
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 4 \
        --worker-class gevent \
        --worker-connections 1000 \
        --timeout 120 \
        --keepalive 5 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --log-level info \
        --capture-output \
        "ark_tools.api.app:create_app()"
fi