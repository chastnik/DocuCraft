#!/bin/bash

# Script to start DocuCraft services

set -e

echo "🚀 Starting DocuCraft..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
    exit 1
fi

# Check if database is running
echo "🔍 Checking database connection..."
python3 -c "
import sys
from app.core.config import settings
try:
    import asyncpg
    import asyncio
    async def check():
        conn = await asyncpg.connect(settings.database_url.replace('+asyncpg', '').replace('postgresql+asyncpg://', 'postgresql://'))
        await conn.close()
    asyncio.run(check())
    print('✅ Database connection OK')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
" || exit 1

# Run migrations
echo "📦 Running database migrations..."
alembic upgrade head || {
    echo "❌ Migration failed"
    exit 1
}

# Start Celery worker in background
echo "🔄 Starting Celery worker..."
celery -A app.tasks.celery_app worker --loglevel=info --detach --pidfile=celery.pid

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📚 API documentation: http://localhost:8000/docs"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

