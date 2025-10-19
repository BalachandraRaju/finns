#!/bin/bash

# Finns Application Deployment Script

set -e

echo "🚀 Finns Application Deployment"
echo "================================"

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

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration before running again."
    echo "   Required: UPSTOX_ACCESS_TOKEN, TELEGRAM_BOT_TOKEN (optional)"
    exit 1
fi

echo "📦 Building Docker images..."
docker-compose build

echo "🗄️  Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Application URLs:"
    echo "   Web Interface: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Redis: localhost:6379"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f app"
    echo ""
    echo "🛑 Stop services:"
    echo "   docker-compose down"
else
    echo "❌ Failed to start services. Check logs:"
    docker-compose logs
    exit 1
fi
