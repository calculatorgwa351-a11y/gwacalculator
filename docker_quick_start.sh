#!/bin/bash

echo "🐳 GWA Calculator - Docker Quick Start"
echo "======================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Choose deployment mode
echo "🚀 Choose deployment mode:"
echo "1) Basic (SQLite only)"
echo "2) With PostgreSQL"
echo "3) With Redis caching"
echo "4) Full stack (PostgreSQL + Redis)"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "🔧 Starting basic setup..."
        docker-compose up --build
        ;;
    2)
        echo "🗄️ Starting with PostgreSQL..."
        docker-compose --profile postgres up --build
        ;;
    3)
        echo "💾 Starting with Redis..."
        docker-compose --profile redis up --build
        ;;
    4)
        echo "🚀 Starting full stack..."
        docker-compose --profile postgres --profile redis up --build
        ;;
    *)
        echo "❌ Invalid choice. Starting basic setup..."
        docker-compose up --build
        ;;
esac

echo ""
echo "✅ Setup complete!"
echo "🌐 Application: http://localhost:5000"
echo "👤 Admin login: admin / adminpass"
echo "🎓 Student login: 2024xxxx / password123"
echo ""
echo "📊 Data analysis endpoints available at:"
echo "   - /api/analytics/all_data"
echo "   - /api/analytics/summary"
echo "   - /api/analytics/export/csv"
echo ""
echo "🛑 To stop: docker-compose down"
echo "📋 To view logs: docker-compose logs -f"
