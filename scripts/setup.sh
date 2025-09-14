#!/bin/bash

# Market Tracker Setup Script
# This script sets up the development environment

set -e

echo "🚀 Setting up Market Tracker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p data/postgres
mkdir -p data/grafana
mkdir -p data/redis

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your configuration"
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if services are running
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec postgres pg_isready -U postgres; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check FastAPI
if curl -f http://localhost:8000/api/v1/health/live > /dev/null 2>&1; then
    echo "✅ FastAPI is ready"
else
    echo "❌ FastAPI is not ready"
fi

# Check Grafana
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is ready"
else
    echo "❌ Grafana is not ready"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📊 Services available at:"
echo "  - FastAPI: http://localhost:8000"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "📚 Next steps:"
echo "  1. Visit http://localhost:8000 to see the API documentation"
echo "  2. Visit http://localhost:3000 to access Grafana dashboards"
echo "  3. Check logs with: docker-compose logs -f"
echo "  4. Stop services with: docker-compose down"
echo ""
