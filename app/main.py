from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base, SessionLocal
from app.models import Department, Course, User, Admin
from app.routers import pages, api
import os

app = FastAPI(title="GWA Calculator", version="2.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(api.router)

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
        
        # Create admin user
        admin_user = db.query(User).filter(User.school_id == 'admin').first()
        if not admin_user:
            admin_user = User(school_id='admin', name='Administrator', department='COTE', course='Administration')
            admin_user.set_password('adminpass')
            db.add(admin_user)
            db.commit()
            print("✅ Created admin user: admin / adminpass")
            
            # Grant admin rights
            admin_record = Admin(user_id=admin_user.id)
            db.add(admin_record)
            db.commit()
            print("✅ Granted admin rights")
        else:
            print("✅ Admin user already exists")
        
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
