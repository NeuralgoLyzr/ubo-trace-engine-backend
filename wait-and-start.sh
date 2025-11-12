#!/bin/bash

# Script to wait for Docker and then start containers

echo "🔍 Checking Docker status..."
MAX_WAIT=120  # 2 minutes max wait
WAIT_COUNT=0

while ! docker info > /dev/null 2>&1; do
    if [ $WAIT_COUNT -eq 0 ]; then
        echo "⏳ Waiting for Docker Desktop to start..."
        echo "   Please open Docker Desktop if it's not already running."
    fi
    
    sleep 2
    WAIT_COUNT=$((WAIT_COUNT + 2))
    
    if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
        echo "❌ Docker did not start within $MAX_WAIT seconds."
        echo "   Please start Docker Desktop manually and run: docker-compose up --build -d"
        exit 1
    fi
    
    # Show progress every 10 seconds
    if [ $((WAIT_COUNT % 10)) -eq 0 ]; then
        echo "   Still waiting... (${WAIT_COUNT}s)"
    fi
done

echo "✅ Docker is running!"
echo ""
echo "🔨 Starting containers..."
cd "$(dirname "$0")"
docker-compose up --build -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "📋 Checking services..."
echo ""
echo "MongoDB logs (last 5 lines):"
docker-compose logs --tail=5 mongodb 2>&1 | tail -5

echo ""
echo "Backend logs (last 10 lines):"
docker-compose logs --tail=10 app 2>&1 | tail -10

echo ""
echo "🧪 Testing API..."
sleep 5
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo "🌐 API: http://localhost:8000"
    echo "📚 Docs: http://localhost:8000/docs"
else
    echo "⏳ API is still starting... (check logs with: docker-compose logs -f app)"
fi

echo ""
echo "📝 Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   View app logs:    docker-compose logs -f app"
echo "   View DB logs:     docker-compose logs -f mongodb"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo ""


