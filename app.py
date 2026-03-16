#!/usr/bin/env python3
"""
FastAPI GWA Calculator Application
High-performance replacement for Flask with the same design and functionality
"""

from fastapi import FastAPI, Request, Depends, HTTPException, Form, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, List
import os
import random
from functools import lru_cache
import ssl
import certifi

# Initialize FastAPI app
app = FastAPI(title="GWA Calculator", version="2.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBasic()

# Database Configuration
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database configuration
    PGUSER = os.getenv('PGUSER')
    PGPASSWORD = os.getenv('PGPASSWORD')
    PGHOST = os.getenv('PGHOST')
    PGPORT = os.getenv('PGPORT', '5432')
    PGDATABASE = os.getenv('PGDATABASE')
    SUPABASE_SSL_NO_VERIFY = os.getenv('SUPABASE_SSL_NO_VERIFY', '0').lower() in ("1", "true", "yes")
    
    @property
    def database_url(self):
        if self.PGUSER and self.PGPASSWORD and self.PGHOST and self.PGPORT and self.PGDATABASE:
            # Use PostgreSQL (Supabase)
            if self.SUPABASE_SSL_NO_VERIFY:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            else:
                ctx = ssl.create_default_context(cafile=certifi.where())
            
            return f"postgresql+pg8000://{self.PGUSER}:{self.PGPASSWORD}@{self.PGHOST}:{self.PGPORT}/{self.PGDATABASE}?ssl_context={ctx}"
        else:
            # Use SQLite for local development
            return "sqlite:///gwa_calculator.db"

config = Config()

# Database setup
engine = create_engine(config.database_url, pool_pre_ping=True, pool_recycle=300, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    password_hash = Column(String(128), nullable=False)
    department = Column(String(64))
    course = Column(String(128))
    
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    grades = relationship("SubjectGrade", back_populates="student", cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Department(Base):
    __tablename__ = 'department'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False)
    
    courses = relationship("Course", back_populates="department")

class Course(Base):
    __tablename__ = 'course'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    department_id = Column(Integer, ForeignKey('department.id'))
    
    department = relationship("Department", back_populates="courses")

class Post(Base):
    __tablename__ = 'post'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("User", back_populates="posts")
    reactions = relationship("Reaction", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

class Reaction(Base):
    __tablename__ = 'reaction'
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    type = Column(String(32), default='like')
    
    post = relationship("Post", back_populates="reactions")

class Comment(Base):
    __tablename__ = 'comment'
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey('post.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    post = relationship("Post", back_populates="comments")
    author = relationship("User")

class SubjectGrade(Base):
    __tablename__ = 'subject_grade'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    subject = Column(String(128), nullable=False)
    units = Column(Float, default=3.0)
    grade = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    student = relationship("User", back_populates="grades")
    
    def is_failed(self):
        return self.grade is not None and self.grade > 3.0

class Admin(Base):
    __tablename__ = 'admin'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('user.id'), unique=True)
    
    user = relationship("User")

# Pydantic models for API
class UserCreate(BaseModel):
    school_id: str
    name: str
    password: str
    department: Optional[str] = None
    course: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    school_id: str
    name: str
    department: Optional[str]
    course: Optional[str]
    
    class Config:
        from_attributes = True

class GradeCreate(BaseModel):
    subject: str
    units: float = 3.0
    grade: float

class GradeResponse(BaseModel):
    id: int
    subject: str
    units: float
    grade: float
    timestamp: datetime
    failed: bool
    
    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    content: str

class PostResponse(BaseModel):
    id: int
    content: str
    author: str
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Utility functions
@lru_cache(maxsize=128)
def compute_gwa_for_user(user_id: int, db: Session) -> Optional[float]:
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user_id).all()
    total_units = sum(g.units for g in grades if g.units is not None and g.grade is not None)
    if total_units == 0:
        return None
    total = sum(g.units * g.grade for g in grades if g.units is not None and g.grade is not None)
    return round(total / total_units, 3)

@lru_cache(maxsize=128)
def analyze_latin_honors(user_id: int, db: Session) -> dict:
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user_id).all()
    if not grades:
        return {"eligible": False, "reason": "No grades recorded", "title": None}

    total_units = 0
    total_weighted_grade = 0
    has_failed = False
    has_below_2_5 = False

    for g in grades:
        if g.grade is None or g.units is None:
            continue

        # Exclude NSTP/ROTC from GWA
        subj_upper = (g.subject or "").upper()
        if "NSTP" in subj_upper or "ROTC" in subj_upper:
            continue

        total_units += g.units
        total_weighted_grade += (g.units * g.grade)

        if g.grade > 3.0:
            has_failed = True
        if g.grade > 2.5:
            has_below_2_5 = True

    if total_units == 0:
        return {"eligible": False, "reason": "No valid academic units", "title": None, "status": "Regular"}

    gwa = round(total_weighted_grade / total_units, 3)
    status = "Regular"

    if has_failed:
        return {"eligible": False, "reason": "Has failing grades (>3.0)", "title": None, "gwa": gwa, "status": status}
    
    if has_below_2_5:
        return {"eligible": False, "reason": "Has grades below 2.50", "title": None, "gwa": gwa, "status": status}

    title = None
    if 1.00 <= gwa <= 1.20:
        title = "Summa Cum Laude"
    elif 1.21 <= gwa <= 1.45:
        title = "Magna Cum Laude"
    elif 1.46 <= gwa <= 1.75:
        title = "Cum Laude"

    if title:
        return {"eligible": True, "reason": "Meets all CTU academic criteria", "title": title, "gwa": gwa, "status": status}
    else:
        return {"eligible": False, "reason": "GWA does not meet honors cutoff", "title": None, "gwa": gwa, "status": status}

# Session management (simple in-memory session for demo)
sessions = {}

def get_current_user(request: Request, db: Session):
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        user_id = sessions[session_id]
        user = db.query(User).filter(User.id == user_id).first()
        return user
    return None

def is_admin(user: User, db: Session) -> bool:
    if not user:
        return False
    return db.query(Admin).filter(Admin.user_id == user.id).first() is not None

# Routes
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "session": {"user_id": user.id if user else None}
    })

@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db), school_id: str = Form(...), password: str = Form(...)):
    user = db.query(User).filter(User.school_id == school_id).first()
    if user and user.check_password(password):
        # Create session
        session_id = f"session_{user.id}_{datetime.now().timestamp()}"
        sessions[session_id] = user.id
        
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie("session_id", session_id, max_age=3600)  # 1 hour
        return response
    
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    # Get departments
    departments = db.query(Department).all()
    
    # Get posts with eager loading
    posts = db.query(Post).join(User).order_by(Post.timestamp.desc()).limit(5).all()
    
    # Get user's grades
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user.id).limit(10).all()
    
    # Calculate GWA and honors
    gwa = compute_gwa_for_user(user.id, db)
    honors = analyze_latin_honors(user.id, db)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "session": {"user_id": user.id},
        "departments": departments,
        "posts": posts,
        "grades": grades,
        "gwa": gwa,
        "honors": honors
    })

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session_id")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "session": {"user_id": user.id}
    })

# API Endpoints
@app.get("/api/posts", response_model=List[PostResponse])
async def get_posts(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    posts = db.query(Post).join(User).order_by(Post.timestamp.desc()).limit(100).all()
    return [{"id": p.id, "content": p.content, "author": p.author.name, "timestamp": p.timestamp} for p in posts]

@app.post("/api/posts", response_model=PostResponse)
async def create_post(request: Request, post: PostCreate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    new_post = Post(user_id=user.id, content=post.content)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return {"id": new_post.id, "content": new_post.content, "author": user.name, "timestamp": new_post.timestamp}

@app.get("/api/grades", response_model=List[GradeResponse])
async def get_grades(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user.id).order_by(SubjectGrade.timestamp.desc()).all()
    return [{"id": g.id, "subject": g.subject, "units": g.units, "grade": g.grade, "timestamp": g.timestamp, "failed": g.is_failed()} for g in grades]

@app.post("/api/grades", response_model=GradeResponse)
async def create_grade(request: Request, grade: GradeCreate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Clear cache for this user
    compute_gwa_for_user.cache_clear()
    analyze_latin_honors.cache_clear()
    
    new_grade = SubjectGrade(user_id=user.id, subject=grade.subject, units=grade.units, grade=grade.grade)
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    
    return {"id": new_grade.id, "subject": new_grade.subject, "units": new_grade.units, "grade": new_grade.grade, "timestamp": new_grade.timestamp, "failed": new_grade.is_failed()}

@app.get("/api/analytics")
async def get_analytics(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    users = db.query(User).all()
    gwas = []
    total_subjects = 0
    failed_subjects = 0
    
    for u in users:
        grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == u.id).all()
        total_subjects += len(grades)
        failed_subjects += sum(1 for g in grades if g.grade > 3.0)
        
        # Calculate GWA
        total_u_units = sum(g.units for g in grades if g.units and g.grade)
        if total_u_units > 0:
            total_points = sum(g.units * g.grade for g in grades if g.units and g.grade)
            gwas.append(round(total_points / total_u_units, 3))
    
    avg_gwa = round(sum(gwas)/len(gwas), 3) if gwas else None
    fail_rate = (failed_subjects/total_subjects) if total_subjects > 0 else None
    
    return {"average_gwa": avg_gwa, "failure_rate": fail_rate}

# Admin APIs
@app.get("/api/admin/students", response_model=List[UserResponse])
async def get_students(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    students = db.query(User).all()
    return [{"id": u.id, "school_id": u.school_id, "name": u.name, "department": u.department, "course": u.course} for u in students]

@app.post("/api/admin/students", response_model=UserResponse)
async def create_student(request: Request, student: UserCreate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Check if school ID already exists
    existing = db.query(User).filter(User.school_id == student.school_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="School ID already exists")
    
    new_user = User(
        school_id=student.school_id,
        name=student.name,
        department=student.department,
        course=student.course
    )
    new_user.set_password(student.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "school_id": new_user.school_id, "name": new_user.name, "department": new_user.department, "course": new_user.course}

# Database initialization
def init_database():
    """Initialize database with basic structure and admin user"""
    print("🗄️ Initializing FastAPI database...")
    
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create departments and courses (8 courses total)
        departments_data = [
            {'name': 'COTE', 'courses': ['Computer Science', 'Computer Engineering']},
            {'name': 'Business', 'courses': ['Business Administration', 'Accountancy']},
            {'name': 'Liberal Arts', 'courses': ['Psychology', 'Communication Arts']},
            {'name': 'Engineering', 'courses': ['Civil Engineering', 'Electrical Engineering']}
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

if __name__ == "__main__":
    import uvicorn
    
    # Initialize database
    init_database()
    
    # Run the application
    uvicorn.run(app, host="0.0.0.0", port=5000)
