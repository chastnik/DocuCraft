#!/bin/bash

# Script to start DocuCraft services

set +e  # Don't exit on error for service checks

echo "🚀 Starting DocuCraft..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    SUDO_CMD="sudo"
else
    SUDO_CMD=""
fi

# Check if systemd is available
has_systemd() {
    if [ -d /run/systemd/system ] && systemctl is-system-running >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Check PostgreSQL service status
check_postgresql_service() {
    echo "🔍 Checking PostgreSQL service..."
    
    # First, try to connect directly (most reliable check)
    if command -v psql >/dev/null 2>&1; then
        if psql -l >/dev/null 2>&1; then
            echo "✅ PostgreSQL is accessible"
            return 0
        fi
        if sudo -u postgres psql -l >/dev/null 2>&1; then
            echo "✅ PostgreSQL is accessible (as postgres user)"
            return 0
        fi
    fi
    
    # If direct connection failed, try to start service
    if has_systemd; then
        if systemctl is-active --quiet postgresql 2>/dev/null || \
           systemctl is-active --quiet postgresql@main 2>/dev/null; then
            echo "✅ PostgreSQL service is running (systemd)"
        else
            echo "⚠️  Starting PostgreSQL service..."
            $SUDO_CMD systemctl start postgresql 2>/dev/null || \
            $SUDO_CMD systemctl start postgresql@main 2>/dev/null || true
            sleep 2
        fi
    elif command -v service >/dev/null 2>&1; then
        if service postgresql status >/dev/null 2>&1; then
            echo "✅ PostgreSQL service is running (service)"
        else
            echo "⚠️  Starting PostgreSQL service..."
            $SUDO_CMD service postgresql start 2>/dev/null || true
            sleep 2
        fi
    fi
    
    # Final check
    if command -v psql >/dev/null 2>&1; then
        sleep 1
        if psql -l >/dev/null 2>&1 || sudo -u postgres psql -l >/dev/null 2>&1; then
            echo "✅ PostgreSQL is now accessible"
            return 0
        fi
    fi
    
    return 1
}

# Check Redis service status
check_redis_service() {
    echo "🔍 Checking Redis service..."
    
    # First, try to connect directly
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis is accessible"
            return 0
        fi
    fi
    
    # If direct connection failed, try to start service
    if has_systemd; then
        if systemctl is-active --quiet redis 2>/dev/null || \
           systemctl is-active --quiet redis-server 2>/dev/null; then
            echo "✅ Redis service is running (systemd)"
        else
            echo "⚠️  Starting Redis service..."
            $SUDO_CMD systemctl start redis-server 2>/dev/null || \
            $SUDO_CMD systemctl start redis 2>/dev/null || true
            sleep 1
        fi
    elif command -v service >/dev/null 2>&1; then
        if service redis status >/dev/null 2>&1 || \
           service redis-server status >/dev/null 2>&1; then
            echo "✅ Redis service is running (service)"
        else
            echo "⚠️  Starting Redis service..."
            $SUDO_CMD service redis-server start 2>/dev/null || \
            $SUDO_CMD service redis start 2>/dev/null || true
            sleep 1
        fi
    fi
    
    # Final check
    if command -v redis-cli >/dev/null 2>&1; then
        sleep 1
        if redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis is now accessible"
            return 0
        fi
    fi
    
    return 1
}

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
    elif [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "❌ env.example file not found. Cannot create .env"
        exit 1
    fi
    echo "📝 Please edit .env file with your configuration"
    exit 1
fi

# Check PostgreSQL
if ! check_postgresql_service; then
    echo "❌ PostgreSQL is not accessible"
    echo "   Please ensure PostgreSQL is running:"
    if has_systemd; then
        echo "   sudo systemctl start postgresql"
    elif command -v service >/dev/null 2>&1; then
        echo "   sudo service postgresql start"
    fi
    exit 1
fi

# Check Redis (required for Celery)
if ! check_redis_service; then
    echo "⚠️  Redis is not accessible (required for Celery)"
    echo "   Celery worker may not function properly"
    echo "   Please ensure Redis is running:"
    if has_systemd; then
        echo "   sudo systemctl start redis"
    elif command -v service >/dev/null 2>&1; then
        echo "   sudo service redis start"
    fi
    echo "   Continuing anyway..."
fi

# From now on, exit on error
set -e

# Check database connection using Python (more reliable with actual credentials)
echo "🔍 Verifying database connection..."
python3 -c "
import sys
from app.core.config import settings
try:
    import asyncpg
    import asyncio
    from sqlalchemy.engine.url import make_url
    
    async def check():
        # Use SQLAlchemy's URL parser (handles special characters correctly)
        db_url = settings.database_url
        # Remove asyncpg driver if present for parsing
        if '+asyncpg' in db_url:
            db_url_for_parse = db_url.replace('+asyncpg', '')
        elif 'postgresql+asyncpg://' in db_url:
            db_url_for_parse = db_url.replace('postgresql+asyncpg://', 'postgresql://')
        else:
            db_url_for_parse = db_url
        
        # Parse URL using SQLAlchemy (handles URL encoding properly)
        parsed_url = make_url(db_url_for_parse)
        
        # Extract connection parameters
        host = parsed_url.host or 'localhost'
        port = parsed_url.port or 5432
        user = parsed_url.username or 'postgres'
        password = parsed_url.password or ''
        database = (parsed_url.database or 'postgres').lstrip('/')
        
        # Connect using parameters (more reliable than URL string)
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        await conn.close()
    
    asyncio.run(check())
    print('✅ Database connection OK')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    print('')
    print('Common issues:')
    print('1. Database credentials in .env are incorrect')
    print('2. Database does not exist')
    print('3. PostgreSQL is not accepting connections')
    print('4. Password contains special characters (should be URL encoded)')
    print('')
    print('Run ./scripts/setup.sh to auto-configure database')
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
# Check if Celery is already running
if [ -f celery.pid ] && kill -0 "$(cat celery.pid 2>/dev/null)" 2>/dev/null; then
    CELERY_PID=$(cat celery.pid)
    echo "⚠️  Celery worker is already running (PID: $CELERY_PID)"
    echo "   Stopping old worker..."
    kill "$CELERY_PID" 2>/dev/null || true
    rm -f celery.pid
fi
celery -A app.tasks.celery_app worker --loglevel=info --detach --pidfile=celery.pid
# Wait a moment for PID file to be created
sleep 1
if [ -f celery.pid ]; then
    CELERY_PID=$(cat celery.pid)
    echo "✅ Celery worker started (PID: $CELERY_PID)"
else
    echo "⚠️  Celery worker started but PID file not found"
fi

# Setup signal handlers for graceful shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    if [ -f celery.pid ]; then
        CELERY_PID=$(cat celery.pid)
        if kill -0 "$CELERY_PID" 2>/dev/null; then
            echo "   Stopping Celery worker (PID: $CELERY_PID)..."
            kill "$CELERY_PID" 2>/dev/null || true
            rm -f celery.pid
        fi
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start FastAPI server
echo "🌐 Starting FastAPI server..."
echo "📚 API documentation: http://localhost:8000/docs"
echo "💡 Press Ctrl+C to stop all services"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

