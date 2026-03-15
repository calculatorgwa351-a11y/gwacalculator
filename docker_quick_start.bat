@echo off
title GWA Calculator - Docker Quick Start

echo 🐳 GWA Calculator - Docker Quick Start
echo ======================================
echo.

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running.
    echo Please install Docker Desktop first.
    pause
    exit /b 1
)

echo 🚀 Choose deployment mode:
echo 1) Supabase PostgreSQL (Production)
echo 2) Local PostgreSQL (Development)
echo 3) With Redis caching
echo 4) Full stack (PostgreSQL + Redis)
echo.
set /p choice="Enter choice (1-4): "

if "%choice%"=="1" (
    echo �️ Starting with Supabase PostgreSQL...
    docker-compose up --build
) else if "%choice%"=="2" (
    echo 🗄️ Starting with local PostgreSQL...
    docker-compose --profile local-postgres up --build
) else if "%choice%"=="3" (
    echo 💾 Starting with Redis...
    docker-compose --profile redis up --build
) else if "%choice%"=="4" (
    echo 🚀 Starting full stack...
    docker-compose --profile local-postgres --profile redis up --build
) else (
    echo ❌ Invalid choice. Starting with Supabase...
    docker-compose up --build
)

echo.
echo ✅ Setup complete!
echo 🌐 Application: http://localhost:5000
echo 👤 Admin login: admin / adminpass
echo 🎓 Student login: 2024xxxx / password123
echo.
echo 📊 Data analysis endpoints available at:
echo    - /api/analytics/all_data
echo    - /api/analytics/summary
echo    - /api/analytics/export/csv
echo.
echo 🛑 To stop: docker-compose down
echo 📋 To view logs: docker-compose logs -f
pause
