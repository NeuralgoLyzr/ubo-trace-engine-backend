#!/bin/bash

# Script to run UBO Trace Engine Backend with Docker

set -e

echo "🐳 Starting UBO Trace Engine Backend with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker daemon is not running."
    echo "   Please start Docker Desktop and wait until it's fully started."
    exit 1
fi

echo "✓ Docker is running"

# Navigate to project directory
cd "$(dirname "$0")"

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start containers
echo "🔨 Building and starting containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Services are running!"
    echo ""
    echo "📋 Container Status:"
    docker-compose ps
    echo ""
    echo "🌐 API available at: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo "🔍 UBO Search endpoint: POST http://localhost:8000/api/v1/search-ubo"
    echo ""
    echo "📊 Useful commands:"
    echo "   View logs:        docker-compose logs -f"
    echo "   View app logs:   docker-compose logs -f app"
    echo "   View DB logs:     docker-compose logs -f mongodb"
    echo "   Stop services:   docker-compose down"
    echo "   Restart:          docker-compose restart"
    echo ""
else
    echo "❌ Services failed to start. Check logs with:"
    echo "   docker-compose logs"
fi

