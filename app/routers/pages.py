from fastapi import APIRouter, Request, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user, is_admin
from app.models import Department, Post, User, SubjectGrade
from app.crud import compute_gwa_for_user, analyze_latin_honors

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "session": {"user_id": user.id if user else None}
    })

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    departments = db.query(Department).all()
    return templates.TemplateResponse("register.html", {
        "request": request,
        "departments": departments,
        "session": {"user_id": None}
    })

@router.post("/register")
async def api_register(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    school_id = form.get("school_id")
    name = form.get("name")
    department = form.get("department")
    course = form.get("course")
    password = form.get("password")

    if not all([school_id, name, password]):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Missing required fields",
            "departments": db.query(Department).all()
        })

    # Check if exists
    existing = db.query(User).filter(User.school_id == school_id).first()
    if existing:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "School ID already registered",
            "departments": db.query(Department).all()
        })

    new_user = User(
        school_id=school_id,
        name=name,
        department=department,
        course=course
    )
    new_user.set_password(password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Assign 8 default subjects
    import random
    default_subjects = [
        "Data Structures and Algorithms", "Database Systems", "Operating Systems", 
        "Computer Organization", "Software Engineering", "Web Development", 
        "Artificial Intelligence", "Network Security"
    ]
    for subject in default_subjects:
        grade = round(random.uniform(1.0, 3.0), 2)
        new_grade = SubjectGrade(
            user_id=new_user.id,
            subject=subject,
            units=3.0,
            grade=grade,
            year=1,
            semester=1
        )
        db.add(new_grade)
    db.commit()

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/dashboard", response_class=HTMLResponse)
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

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "session": {"user_id": user.id}
    })
