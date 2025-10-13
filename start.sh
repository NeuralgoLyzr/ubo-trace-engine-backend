#!/bin/bash

# UBO Trace Engine Backend - Quick Start Script

echo "🚀 Starting UBO Trace Engine Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if MongoDB is running
if ! command -v mongod &> /dev/null && ! docker ps | grep -q mongo; then
    echo "⚠️  MongoDB is not running. Starting MongoDB with Docker..."
    docker run -d -p 27017:27017 --name ubo-mongodb mongo:7.0
    sleep 5
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists, if not create from template
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env .env.backup 2>/dev/null || true
fi

# Start the application
echo "🎯 Starting UBO Trace Engine Backend..."
echo "📚 API Documentation will be available at: http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
