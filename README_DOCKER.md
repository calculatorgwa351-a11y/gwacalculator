# 🐳 GWA Calculator - Docker Deployment

## 🚀 Quick Start with Docker

### Basic Setup (SQLite)
```bash
# Build and start the application
docker-compose up --build
```

### With PostgreSQL Database
```bash
# Start with PostgreSQL
docker-compose --profile postgres up --build
```

### With Redis Caching
```bash
# Start with Redis
docker-compose --profile redis up --build
```

### Full Stack (App + PostgreSQL + Redis)
```bash
# Start all services
docker-compose --profile postgres --profile redis up --build
```

## 🎯 What Docker Setup Does Automatically

### 🔄 One-Command Initialization
The Docker setup handles everything automatically:

1. **📦 Dependency Installation** - Installs Flask, SQLAlchemy, Faker, etc.
2. **🗄️ Database Creation** - Creates all necessary tables
3. **🏛️️ Department Setup** - Creates 5 departments with courses
4. **👥 Admin Account** - Creates admin user (admin / adminpass)
5. **📊 Dummy Data Generation** - Creates 50+ realistic student accounts
6. **🎓 Academic Data** - Generates grades with realistic distributions
7. **💬 Social Content** - Creates posts, reactions, comments
8. **🚀 Application Start** - Launches the Flask app
9. **💚 Health Checks** - Monitors application health

### 📊 Generated Data Includes

- **50+ Students** across 5 departments
- **Realistic Filipino Names** and school IDs (2024xxxx format)
- **Academic Performance** with subject-specific difficulty curves
- **Social Interactions** including posts, reactions, and comments
- **Time-based Data** spanning the past academic year
- **Department Structure**: COTE, Business, Liberal Arts, Engineering, Science

## 🔑 Access Information

### Application Access
- **URL**: http://localhost:5000
- **Admin Login**: admin / adminpass
- **Student Login**: 2024xxxx / password123

### Database Access
- **SQLite** (default): `./instance/app.db`
- **PostgreSQL**: localhost:5432 (when using postgres profile)
  - Database: gwacalculator
  - User: gwauser
  - Password: gwasecret

### Redis Access (when using redis profile)
- **URL**: localhost:6379

## 📈 Data Analysis Endpoints

Once running, access these comprehensive analytics endpoints:

- **`GET /api/analytics/all_data`** - Complete dataset export
- **`GET /api/analytics/summary`** - Comprehensive analytics dashboard
- **`GET /api/analytics/export/csv`** - Download CSV for external analysis
- **`GET /api/analytics/department_avg`** - Department performance comparison
- **`GET /api/analytics/failure_rates`** - Subject difficulty analysis
- **`GET /api/analytics/gwa_trends?user_id=1`** - Individual student progress

## 🛠️ Development Commands

### Build Only
```bash
docker-compose build
```

### Start Services
```bash
# Basic setup
docker-compose up

# With database
docker-compose --profile postgres up

# With Redis
docker-compose --profile redis up

# All services
docker-compose --profile postgres --profile redis up
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f app
```

### Rebuild
```bash
docker-compose up --build --force-recreate
```

## 🗄️ Database Persistence

### SQLite (Default)
- Data persists in `./instance/` volume
- Database file: `./instance/app.db`
- To reset: `docker-compose down && rm -rf instance/ && docker-compose up --build`

### PostgreSQL (Optional)
- Data persists in `postgres_data` Docker volume
- Connection strings configured automatically
- Better for production/development teams

## 🔧 Configuration

### Environment Variables
- `FLASK_ENV`: production/development
- `FLASK_DEBUG`: 0/1 (debug mode)
- `PYTHONUNBUFFERED`: 1 (for proper logging)

### Customization
Edit `docker_init.py` to modify:
- Number of dummy students
- Department structure
- Subject lists
- Grade distributions

## 🌐 Production Deployment

### Environment Setup
1. Copy `.env.example` to `.env`
2. Update database credentials in `.env`
3. Set `FLASK_ENV=production`
4. Deploy with PostgreSQL profile

### Render Deployment
The existing `render.yaml` works with Docker:
- Automatically builds from Dockerfile
- Handles environment variables
- Scales with gunicorn

## 🔍 Troubleshooting

### Port Conflicts
If port 5000 is occupied:
```yaml
# In docker-compose.yml, change:
ports:
  - "5001:5000"  # Use different host port
```

### Database Issues
```bash
# Reset database
docker-compose down
docker volume rm gwacalculator_postgres_data  # PostgreSQL only
docker-compose up --build
```

### Health Check Failures
```bash
# Check container status
docker-compose ps

# View health logs
docker-compose logs app
```

### Rebuild Everything
```bash
# Clean rebuild
docker-compose down
docker system prune -f
docker-compose up --build
```

## 📊 Container Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GWA App     │    │   PostgreSQL    │    │     Redis     │
│   (Flask)     │────│  (Optional)    │────│  (Optional)    │
│   Port: 5000   │    │   Port: 5432   │    │   Port: 6379   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        └───────────────────────┴───────────────────────┘
                    gwa-network
```

## 🎉 Benefits of Docker Setup

- **🔄 Reproducible** - Same environment everywhere
- **⚡ Fast Setup** - One command deployment
- **🗄️ Database Ready** - Automatic initialization
- **📊 Data Included** - 50+ realistic test accounts
- **🏥 Production Ready** - Scalable architecture
- **💚 Health Monitoring** - Automatic health checks
- **🔧 Easy Management** - Simple compose commands

---

**Ready for comprehensive academic data analysis!** 🎓📊
