# GWA Calculator

A modern Flask application for students to manage academic grades and share updates. Built with the Philippine GWA system in mind.

## 🚀 Features
- **Smart GWA Calculation**: Automatic weighted average computation.
- **Academic Social Feed**: Share updates, react, and comment on posts.
- **Department/Program View**: Foldable sidebar for program exploration.
- **Admin Console**: System-wide monitoring and student management.
- **Data Analysis Ready**: Comprehensive analytics endpoints for research.
- **Dummy Data Generator**: 50+ realistic test accounts for analysis.

## 🎯 Quick Start (Automated Setup)

### Windows:
```bash
run.bat
```

### Linux/Mac:
```bash
chmod +x run.sh
./run.sh
```

This single command will:
- ✅ Install all dependencies automatically
- ✅ Initialize the database
- ✅ Generate 50+ realistic student accounts
- ✅ Create comprehensive academic and social data
- ✅ Ask if you want to start the app immediately

## � Login Credentials

- **Admin**: `admin` / `adminpass`
- **Students**: `2024xxxx` / `password123` (any 2024xxxx school ID)

## 📊 Data Analysis Endpoints

- **`GET /api/analytics/all_data`** - Complete dataset export
- **`GET /api/analytics/summary`** - Comprehensive analytics dashboard
- **`GET /api/analytics/export/csv`** - Download CSV for external analysis
- **`GET /api/analytics/department_avg`** - Department performance comparison
- **`GET /api/analytics/failure_rates`** - Subject difficulty analysis
- **`GET /api/analytics/gwa_trends?user_id=1`** - Individual student progress

## 🎓 Generated Data Includes:

- **50+ Students** across 5 departments (COTE, Business, Liberal Arts, Engineering, Science)
- **Realistic Filipino Names** and school IDs
- **Academic Performance** with subject-specific difficulty curves
- **Social Interactions** including posts, reactions, and comments
- **Time-based Data** spanning the past academic year

## 💻 Manual Setup (Optional)

If you prefer manual setup:

```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Initialize database and seed sample data
python init_db.py

# Generate dummy data (optional)
python create_dummy_data.py

# Start the development server
python app.py
```

## 🌐 Access

- **Application**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
- **API Documentation**: Available at `/api/` endpoints

## 📈 Sample Analytics

The `/api/analytics/summary` endpoint provides:
- Total users, grades, posts, reactions, comments
- GWA statistics (average, min, max)
- Department-wise performance metrics
- Subject difficulty and failure rates
- Social engagement scores

## 🛠️ Development

The application uses:
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Default database (easily switchable to PostgreSQL)
- **Faker** - Realistic dummy data generation

---