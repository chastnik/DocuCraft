#!/bin/bash

# Setup script for DocuCraft

set -e

echo "🔧 Setting up DocuCraft..."

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
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Create storage directory
echo "📁 Creating storage directory..."
mkdir -p storage

# Create database if it doesn't exist
echo "🗄️  Setting up database..."
if command -v createdb &> /dev/null; then
    createdb docucraft 2>/dev/null || echo "Database already exists or createdb not available"
else
    echo "⚠️  createdb not found. Please create database manually:"
    echo "   createdb docucraft"
fi

# Run migrations
echo "🔄 Running migrations..."
alembic upgrade head || {
    echo "⚠️  Migrations failed. Make sure database is running and configured in .env"
}

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Make sure PostgreSQL and Redis are running"
echo "3. Run: ./scripts/start.sh"
echo "   or: uvicorn app.main:app --reload"

