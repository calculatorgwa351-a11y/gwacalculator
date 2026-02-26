# GWAcalculator

A modern Flask application for students to manage academic grades and share updates. Built with the Philippine GWA system in mind.

## 🚀 Features
- **Smart GWA Calculation**: Automatic weighted average computation.
- **Academic Social Feed**: Share updates, react, and comment on posts.
- **Department/Program View**: Foldable sidebar for program exploration.
- **Admin Console**: System-wide monitoring and student management.
- **Database Fallback**: Built-in support for Supabase (PostgreSQL) with SQLite fallback for offline development.
- **Cloud Ready**: Pre-configured for deployment on Render.

## 💻 Local Development

### 1. Environment Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file (see `.env.example` if available, or use the template below):
```env
FLASK_DEBUG=1
SECRET_KEY=your-dev-key
# Postgres (optional, falls back to SQLite)
PGUSER=...
PGPASSWORD=...
PGHOST=...
PGPORT=...
PGDATABASE=...
```

### 3. Initialize & Run
```powershell
# Initialize database and seed sample data
python init_db.py

# Start the development server
python app.py
```
Open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in your browser.

## 🌐 Deployment
This project is ready for **Render**.
1. Push to GitHub: `https://github.com/calculatorgwa351-a11y/gwacalculator`
2. Connect to Render.
3. The `render.yaml` and `Procfile` will handle the rest.

---
© 2026 calculatorgwa351-a11y