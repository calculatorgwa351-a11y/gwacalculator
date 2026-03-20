from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base, SessionLocal
from app.models import Department, Course, User, Admin
from app.routers import api
import os
from pathlib import Path

app = FastAPI(
    title="GWA Calculator", 
    version="2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api.router)

# Serve the built SPA (Docker/production)
DIST_DIR = Path("dist")
if DIST_DIR.exists():
    @app.get("/")
    async def serve_index():
        return FileResponse(DIST_DIR / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Never treat /api/* as frontend routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)

        candidate = DIST_DIR / full_path
        if candidate.is_file():
            return FileResponse(candidate)

        return FileResponse(DIST_DIR / "index.html")

# Database initialization
def init_database():
    """Initialize database with basic structure and admin user"""
    print("🗄️ Initializing FastAPI database...")
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create departments and courses (COTE, COED, CBM)
        departments_data = [
            {'name': 'COTE', 'courses': ['Computer Science', 'Computer Engineering']},
            {'name': 'COED', 'courses': ['Elementary Education', 'Secondary Education']},
            {'name': 'CBM', 'courses': ['Business Administration', 'Accountancy']}
        ]
        
        for dept_data in departments_data:
            dept = db.query(Department).filter(Department.name == dept_data['name']).first()
            if not dept:
                dept = Department(name=dept_data['name'])
                db.add(dept)
                db.commit()
                print(f"✅ Created department: {dept.name}")
            
            for course_name in dept_data['courses']:
                course = db.query(Course).filter(Course.name == course_name, Course.department_id == dept.id).first()
                if not course:
                    course = Course(name=course_name, department_id=dept.id)
                    db.add(course)
                    db.commit()
                    print(f"✅ Created course: {course_name} in {dept.name}")
        
        # Create admin user (and ensure admin rights exist)
        admin_user = db.query(User).filter(User.school_id == 'admin').first()
        if not admin_user:
            admin_user = User(
                school_id='admin',
                name='Administrator',
                department='COTE',
                course='Administration'
            )
            admin_user.set_password('adminpass')
            db.add(admin_user)
            db.commit()
            print("✅ Created admin user: admin / adminpass")

        admin_record = db.query(Admin).filter(Admin.user_id == admin_user.id).first()
        if not admin_record:
            admin_record = Admin(user_id=admin_user.id)
            db.add(admin_record)
            db.commit()
            print("✅ Granted admin rights")

        # Check if any students exist
        student_count = db.query(User).filter(User.school_id != 'admin').count()
        if student_count == 0:
                print("⚠️ No students found. Triggering dummy data generation...")
                try:
                    from init import generate_dummy_data
                    generate_dummy_data(db)
                except Exception as e:
                    print(f"❌ Failed to generate dummy data: {e}")
        else:
            # FORCE RESET all users on startup for testing/recovery
            users = db.query(User).all()
            for u in users:
                p = 'adminpass' if u.school_id == 'admin' else 'password123'
                u.set_password(p)
            db.commit()
            print(f"✅ Verified and reset passwords for {len(users)} users")
        
        print("🗄️ FastAPI database initialization complete!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        db.rollback()
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    init_database()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=True)
