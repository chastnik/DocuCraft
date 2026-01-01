#!/bin/bash

# Setup script for DocuCraft

# Don't exit on error for dependency installation (we handle errors manually)
set +e

echo "🔧 Setting up DocuCraft..."

# Detect OS
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
    elif [ -f /etc/lsb-release ]; then
        . /etc/lsb-release
        OS=$DISTRIB_ID
    elif [ -f /etc/debian_version ]; then
        OS=debian
    else
        OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    fi
    echo "$OS"
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "⚠️  Some operations require root privileges. You may be prompted for sudo password."
        SUDO_CMD="sudo"
    else
        SUDO_CMD=""
    fi
}

# Install PostgreSQL
install_postgresql() {
    OS=$(detect_os)
    echo "🐘 Checking PostgreSQL..."
    
    if command -v psql >/dev/null 2>&1; then
        PSQL_VERSION=$(psql --version | awk '{print $3}')
        echo "✅ PostgreSQL already installed: $PSQL_VERSION"
        return 0
    fi
    
    echo "📦 Installing PostgreSQL..."
    
    case $OS in
        debian|ubuntu)
            $SUDO_CMD apt-get update
            $SUDO_CMD apt-get install -y postgresql postgresql-contrib
            ;;
        fedora|rhel|centos)
            if command -v dnf >/dev/null 2>&1; then
                $SUDO_CMD dnf install -y postgresql-server postgresql-contrib
                $SUDO_CMD postgresql-setup --initdb
            else
                $SUDO_CMD yum install -y postgresql-server postgresql-contrib
                $SUDO_CMD postgresql-setup initdb
            fi
            ;;
        arch|manjaro)
            $SUDO_CMD pacman -S --noconfirm postgresql
            $SUDO_CMD -u postgres initdb -D /var/lib/postgres/data
            ;;
        *)
            echo "⚠️  Unsupported OS: $OS. Please install PostgreSQL manually."
            return 1
            ;;
    esac
    
    # Start PostgreSQL service
    echo "🚀 Starting PostgreSQL service..."
    case $OS in
        debian|ubuntu|fedora|rhel|centos|arch|manjaro)
            # Try different service names
            if systemctl list-unit-files | grep -q postgresql.service; then
                $SUDO_CMD systemctl enable postgresql
                $SUDO_CMD systemctl start postgresql
            elif systemctl list-unit-files | grep -q postgresql@.service; then
                $SUDO_CMD systemctl enable postgresql@main || $SUDO_CMD systemctl enable postgresql@13-main || true
                $SUDO_CMD systemctl start postgresql@main || $SUDO_CMD systemctl start postgresql@13-main || true
            fi
            ;;
    esac
    
    if command -v psql >/dev/null 2>&1; then
        PSQL_VERSION=$(psql --version | awk '{print $3}')
        echo "✅ PostgreSQL installed successfully: $PSQL_VERSION"
        return 0
    else
        echo "❌ Failed to install PostgreSQL"
        return 1
    fi
}

# Install Redis
install_redis() {
    OS=$(detect_os)
    echo "🔴 Checking Redis..."
    
    if command -v redis-server >/dev/null 2>&1; then
        REDIS_VERSION=$(redis-server --version 2>/dev/null | awk '{print $3}' | cut -d'=' -f2 || echo "unknown")
        echo "✅ Redis already installed: $REDIS_VERSION"
        return 0
    fi
    
    echo "📦 Installing Redis..."
    
    case $OS in
        debian|ubuntu)
            $SUDO_CMD apt-get update
            $SUDO_CMD apt-get install -y redis-server
            ;;
        fedora|rhel|centos)
            if command -v dnf >/dev/null 2>&1; then
                $SUDO_CMD dnf install -y redis
            else
                $SUDO_CMD yum install -y redis
            fi
            ;;
        arch|manjaro)
            $SUDO_CMD pacman -S --noconfirm redis
            ;;
        *)
            echo "⚠️  Unsupported OS: $OS. Please install Redis manually."
            return 1
            ;;
    esac
    
    # Start Redis service
    echo "🚀 Starting Redis service..."
    case $OS in
        debian|ubuntu|fedora|rhel|centos|arch|manjaro)
            # Try different service names
            if systemctl list-unit-files | grep -q redis-server.service; then
                $SUDO_CMD systemctl enable redis-server
                $SUDO_CMD systemctl start redis-server
            elif systemctl list-unit-files | grep -q redis.service; then
                $SUDO_CMD systemctl enable redis
                $SUDO_CMD systemctl start redis
            fi
            ;;
    esac
    
    if command -v redis-server >/dev/null 2>&1; then
        REDIS_VERSION=$(redis-server --version 2>/dev/null | awk '{print $3}' | cut -d'=' -f2 || echo "unknown")
        echo "✅ Redis installed successfully: $REDIS_VERSION"
        return 0
    else
        echo "❌ Failed to install Redis"
        return 1
    fi
}

# Check and install dependencies
check_root
install_postgresql || echo "⚠️  PostgreSQL installation failed or skipped"
install_redis || echo "⚠️  Redis installation failed or skipped"

# From now on, exit on error (but not for service checks)
set +e

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Python 3.11+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python version OK: $python_version"

# Install dependencies
echo "📦 Installing dependencies..."
if command -v poetry &> /dev/null; then
    echo "Using Poetry..."
    poetry install
else
    echo "Using pip..."
    pip install -r requirements.txt
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    if [ -f env.example ]; then
        cp env.example .env
    elif [ -f .env.example ]; then
        cp .env.example .env
    else
        echo "⚠️  env.example file not found. Creating empty .env file..."
        touch .env
    fi
    echo "⚠️  Please edit .env file with your configuration"
fi

# Create storage directory
echo "📁 Creating storage directory..."
mkdir -p storage

# Check if systemd is available
has_systemd() {
    # Check if systemd is running (not just installed)
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
        # Try multiple connection methods
        if psql -l >/dev/null 2>&1; then
            echo "✅ PostgreSQL is accessible"
            return 0
        fi
        # Try as postgres user (common in containers)
        if sudo -u postgres psql -l >/dev/null 2>&1; then
            echo "✅ PostgreSQL is accessible (as postgres user)"
            return 0
        fi
        # Try connecting to postgres database (most permissive)
        if psql -d postgres -c '\l' >/dev/null 2>&1; then
            echo "✅ PostgreSQL is accessible"
            return 0
        fi
    fi
    
    # If direct connection failed, try to start service
    if has_systemd; then
        # Use systemctl
        if systemctl is-active --quiet postgresql 2>/dev/null || \
           systemctl is-active --quiet postgresql@main 2>/dev/null || \
           systemctl is-active --quiet postgresql@13-main 2>/dev/null; then
            echo "✅ PostgreSQL service is running (systemd)"
        else
            echo "⚠️  PostgreSQL service is not running. Attempting to start..."
            OS=$(detect_os)
            case $OS in
                debian|ubuntu|fedora|rhel|centos|arch|manjaro)
                    if systemctl list-unit-files 2>/dev/null | grep -q postgresql.service; then
                        $SUDO_CMD systemctl start postgresql 2>/dev/null && echo "✅ PostgreSQL started" || true
                    elif systemctl list-unit-files 2>/dev/null | grep -q postgresql@.service; then
                        $SUDO_CMD systemctl start postgresql@main 2>/dev/null || \
                        $SUDO_CMD systemctl start postgresql@13-main 2>/dev/null || true
                    fi
                    sleep 2
                    ;;
            esac
        fi
    elif command -v service >/dev/null 2>&1; then
        # Use service command (for containers without systemd)
        echo "⚠️  systemd not available, using service command..."
        if service postgresql status >/dev/null 2>&1 || \
           service postgresql@main status >/dev/null 2>&1; then
            echo "✅ PostgreSQL service appears to be running (service)"
        else
            echo "⚠️  Attempting to start PostgreSQL with service command..."
            $SUDO_CMD service postgresql start 2>/dev/null || \
            $SUDO_CMD service postgresql@main start 2>/dev/null || \
            $SUDO_CMD service postgresql@13-main start 2>/dev/null || true
            sleep 2
        fi
    else
        echo "⚠️  No service management available. Trying to start PostgreSQL directly..."
        # Try to start PostgreSQL manually
        if [ -f /usr/lib/postgresql/*/bin/postgres ]; then
            # Find postgres binary
            POSTGRES_BIN=$(find /usr/lib/postgresql -name postgres -type f 2>/dev/null | head -1)
            if [ -n "$POSTGRES_BIN" ]; then
                echo "⚠️  Found PostgreSQL binary, but manual start not implemented"
                echo "   Please start PostgreSQL manually or use Docker"
            fi
        fi
    fi
    
    # Final check: try to connect again
    if command -v psql >/dev/null 2>&1; then
        sleep 2
        # Try multiple connection methods
        if psql -l >/dev/null 2>&1; then
            echo "✅ PostgreSQL is now accessible"
            return 0
        elif sudo -u postgres psql -l >/dev/null 2>&1; then
            echo "✅ PostgreSQL is now accessible (as postgres user)"
            return 0
        elif psql -d postgres -c '\l' >/dev/null 2>&1; then
            echo "✅ PostgreSQL is now accessible"
            return 0
        fi
    fi
    
    return 1
}

# Check Redis service status
check_redis_service() {
    echo "🔍 Checking Redis service..."
    
    # First, try to connect directly (most reliable check)
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis is accessible"
            return 0
        fi
    fi
    
    # If direct connection failed, try to start service
    if has_systemd; then
        # Use systemctl
        if systemctl is-active --quiet redis 2>/dev/null || \
           systemctl is-active --quiet redis-server 2>/dev/null; then
            echo "✅ Redis service is running (systemd)"
        else
            echo "⚠️  Redis service is not running. Attempting to start..."
            OS=$(detect_os)
            case $OS in
                debian|ubuntu|fedora|rhel|centos|arch|manjaro)
                    if systemctl list-unit-files 2>/dev/null | grep -q redis-server.service; then
                        $SUDO_CMD systemctl start redis-server 2>/dev/null && echo "✅ Redis started" || true
                    elif systemctl list-unit-files 2>/dev/null | grep -q redis.service; then
                        $SUDO_CMD systemctl start redis 2>/dev/null && echo "✅ Redis started" || true
                    fi
                    sleep 1
                    ;;
            esac
        fi
    elif command -v service >/dev/null 2>&1; then
        # Use service command (for containers without systemd)
        echo "⚠️  systemd not available, using service command..."
        if service redis status >/dev/null 2>&1 || \
           service redis-server status >/dev/null 2>&1; then
            echo "✅ Redis service appears to be running (service)"
        else
            echo "⚠️  Attempting to start Redis with service command..."
            $SUDO_CMD service redis-server start 2>/dev/null || \
            $SUDO_CMD service redis start 2>/dev/null || true
            sleep 1
        fi
    else
        echo "⚠️  No service management available. Trying to start Redis directly..."
        # Try to start Redis manually
        if command -v redis-server >/dev/null 2>&1; then
            echo "⚠️  Found redis-server, but manual start not implemented"
            echo "   Please start Redis manually: redis-server --daemonize yes"
        fi
    fi
    
    # Final check: try to connect again
    if command -v redis-cli >/dev/null 2>&1; then
        sleep 1
        if redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis is now accessible"
            return 0
        fi
    fi
    
    return 1
}

# Setup PostgreSQL user and database
setup_postgresql_db() {
    echo "🔧 Setting up PostgreSQL database and user..."
    
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found. Cannot setup database."
        return 1
    fi
    
    # Extract database URL from .env
    if ! grep -q "DATABASE_URL_SYNC=" .env; then
        echo "⚠️  DATABASE_URL_SYNC not found in .env"
        return 1
    fi
    
    DB_URL=$(grep "DATABASE_URL_SYNC=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
    
    # Check if it's a template
    if [ -z "$DB_URL" ] || echo "$DB_URL" | grep -q "user:password"; then
        echo "⚠️  Database URL in .env appears to be a template."
        echo "   Attempting to setup with default credentials..."
        
        # Try to setup with postgres user
        if sudo -u postgres psql -c '\l' >/dev/null 2>&1; then
            DB_NAME="docucraft"
            DB_USER="docucraft"
            DB_PASSWORD=$(openssl rand -base64 32 2>/dev/null || echo "docucraft_password_$(date +%s)")
            
            echo "   Creating database: $DB_NAME"
            echo "   Creating user: $DB_USER"
            
            # Create user
            sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || \
                sudo -u postgres psql -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || true
            
            # Create database
            sudo -u postgres createdb -O "$DB_USER" "$DB_NAME" 2>/dev/null || true
            
            # Grant privileges
            sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true
            
            # URL encode password to handle special characters
            # Use Python to properly encode the password
            ENCODED_PASSWORD=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$DB_PASSWORD', safe=''))")
            
            # Update .env file with URL-encoded password
            NEW_DB_URL_SYNC="postgresql://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"
            NEW_DB_URL_ASYNC="postgresql+asyncpg://$DB_USER:$ENCODED_PASSWORD@localhost:5432/$DB_NAME"
            sed -i "s|DATABASE_URL_SYNC=.*|DATABASE_URL_SYNC=$NEW_DB_URL_SYNC|" .env
            sed -i "s|DATABASE_URL=.*|DATABASE_URL=$NEW_DB_URL_ASYNC|" .env
            
            echo "✅ Database and user created successfully"
            echo "✅ Updated .env file with new credentials"
            echo ""
            echo "📝 Database credentials:"
            echo "   Database: $DB_NAME"
            echo "   User: $DB_USER"
            echo "   Password: $DB_PASSWORD"
            echo "   (Saved in .env file)"
            return 0
        else
            echo "❌ Cannot connect to PostgreSQL as postgres user"
            return 1
        fi
    fi
    
    return 0
}

# Verify database connection from .env
verify_database_connection() {
    echo "🔍 Verifying database connection..."
    
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found. Skipping database connection check."
        return 1
    fi
    
    # Try to extract database URL from .env
    if grep -q "DATABASE_URL_SYNC=" .env; then
        DB_URL=$(grep "DATABASE_URL_SYNC=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
        
        if [ -z "$DB_URL" ] || echo "$DB_URL" | grep -q "user:password"; then
            echo "⚠️  Database URL in .env appears to be a template."
            echo "   Attempting to setup database automatically..."
            if setup_postgresql_db; then
                # Re-read the updated URL
                DB_URL=$(grep "DATABASE_URL_SYNC=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
            else
                echo "⚠️  Automatic setup failed. Please update .env manually."
                return 1
            fi
        fi
        
        # Try to connect using psql if available
        if command -v psql >/dev/null 2>&1; then
            # Extract connection details
            if echo "$DB_URL" | grep -q "postgresql://"; then
                # Parse URL: postgresql://user:password@host:port/dbname
                DB_NAME=$(echo "$DB_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')
                DB_USER=$(echo "$DB_URL" | sed -n 's|postgresql://\([^:]*\):.*|\1|p')
                DB_PASS=$(echo "$DB_URL" | sed -n 's|postgresql://[^:]*:\([^@]*\)@.*|\1|p')
                DB_HOST=$(echo "$DB_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p')
                DB_PORT=$(echo "$DB_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p' || echo "5432")
                
                if [ -n "$DB_NAME" ]; then
                    # Try to connect
                    export PGPASSWORD="$DB_PASS"
                    if psql -h "$DB_HOST" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" -c '\l' >/dev/null 2>&1; then
                        echo "✅ Database '$DB_NAME' exists and is accessible"
                        unset PGPASSWORD
                        return 0
                    else
                        echo "⚠️  Cannot connect to database '$DB_NAME' with provided credentials"
                        unset PGPASSWORD
                        return 1
                    fi
                fi
            fi
        fi
    else
        echo "⚠️  DATABASE_URL_SYNC not found in .env"
        return 1
    fi
    
    return 0
}

# Create database if it doesn't exist
echo "🗄️  Setting up database..."

# First check if PostgreSQL is running
if ! check_postgresql_service; then
    echo "⚠️  PostgreSQL is not running or not accessible"
    
    # Provide container-specific instructions
    if [ -f /.dockerenv ] || [ -n "$container" ]; then
        echo ""
        echo "💡 You appear to be in a Docker container."
        echo "   PostgreSQL should be running in a separate container or service."
        echo "   Options:"
        echo "   1. Use Docker Compose to start PostgreSQL"
        echo "   2. Connect to external PostgreSQL (update DATABASE_URL_SYNC in .env)"
        echo "   3. Start PostgreSQL in this container:"
        if has_systemd; then
            echo "      sudo systemctl start postgresql"
        elif command -v service >/dev/null 2>&1; then
            echo "      sudo service postgresql start"
        else
            echo "      /usr/lib/postgresql/*/bin/postgres -D /var/lib/postgresql/data"
        fi
    else
        echo "   Please start PostgreSQL manually:"
        if has_systemd; then
            echo "   sudo systemctl start postgresql"
            echo "   or: sudo systemctl start postgresql@main"
        elif command -v service >/dev/null 2>&1; then
            echo "   sudo service postgresql start"
        fi
    fi
    echo ""
    echo "   Then run migrations manually: alembic upgrade head"
fi

# Check Redis
if ! check_redis_service; then
    echo "⚠️  Redis is not running, but continuing anyway (required for Celery)"
    echo "   You can start it manually: sudo systemctl start redis"
fi

# Verify database connection
if ! verify_database_connection; then
    echo "⚠️  Database connection verification failed"
    echo "   Please check your .env file and ensure:"
    echo "   1. DATABASE_URL_SYNC is set correctly"
    echo "   2. Database exists and is accessible"
    echo "   3. PostgreSQL is running"
    echo ""
    echo "   Continuing with migrations anyway..."
fi

# Run migrations (now exit on error)
set -e
echo "🔄 Running migrations..."
if alembic upgrade head 2>&1; then
    echo "✅ Migrations completed successfully"
    set +e
else
    MIGRATION_ERROR=$?
    set +e
    echo "❌ Migrations failed with exit code: $MIGRATION_ERROR"
    echo ""
    echo "Common issues and solutions:"
    echo "1. PostgreSQL is not running:"
    echo "   sudo systemctl start postgresql"
    echo "   or: sudo systemctl start postgresql@main"
    echo ""
    echo "2. Database credentials in .env are incorrect:"
    echo "   - Password authentication failed: The script can auto-create user and database"
    echo "   - Check DATABASE_URL_SYNC in .env file"
    echo "   - If using template values, the script will auto-setup on next run"
    echo "   - Or create manually:"
    echo "     sudo -u postgres psql -c \"CREATE USER docucraft WITH PASSWORD 'your_password';\""
    echo "     sudo -u postgres createdb -O docucraft docucraft"
    echo ""
    echo "3. Database does not exist:"
    echo "   createdb docucraft"
    echo "   or: sudo -u postgres createdb docucraft"
    echo ""
    echo "4. Connection refused:"
    echo "   - Check if PostgreSQL is listening: sudo netstat -tlnp | grep 5432"
    echo "   - Verify DATABASE_URL_SYNC in .env matches your PostgreSQL setup"
    echo ""
    echo "You can run migrations manually later with:"
    echo "  alembic upgrade head"
    echo ""
    echo "⚠️  Setup completed with errors. Please fix the issues above and run migrations manually."
    exit $MIGRATION_ERROR
fi
set +e

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Verify PostgreSQL and Redis are running:"
echo "   - PostgreSQL: sudo systemctl status postgresql"
echo "   - Redis: sudo systemctl status redis"
echo "3. Run: ./scripts/start.sh"
echo "   or: uvicorn app.main:app --reload"
echo ""
echo "💡 Tip: If database connection fails, check your .env file and ensure"
echo "   PostgreSQL is running and accessible."

