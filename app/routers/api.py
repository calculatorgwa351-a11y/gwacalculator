from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import os
from app.database import get_db
from app.auth import (
    create_access_token, get_current_user, 
    is_admin, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models import User, Post, SubjectGrade, Admin, Reaction, Comment
from app.schemas import (
    PostCreate, PostResponse, GradeCreate, GradeResponse, 
    ReactionCreate, CommentCreate, UserCreate, UserResponse, UserUpdate
)
from app.crud import compute_gwa_for_user, analyze_latin_honors, get_global_analytics

router = APIRouter(prefix="/api")

@router.get("/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    """Return the currently authenticated user (derived from JWT cookie)."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {
        "id": user.id,
        "school_id": user.school_id,
        "name": user.name,
        "department": user.department,
        "course": user.course,
        "is_admin": is_admin(user, db)
    }

@router.get("/dashboard/summary")
async def get_dashboard_summary(request: Request, db: Session = Depends(get_db)):
    """Small summary payload for the student dashboard."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    gwa = compute_gwa_for_user(user.id, db)
    honors = analyze_latin_honors(user.id, db)

    grade_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == user.id).count()
    post_count = db.query(Post).filter(Post.user_id == user.id).count()

    return {
        "gwa": gwa,
        "honors": honors,
        "grade_count": grade_count,
        "post_count": post_count
    }

@router.post("/login")
async def api_login(request: Request, db: Session = Depends(get_db)):
    """AJAX/API login endpoint - always returns JSON"""
    try:
        body = await request.form()
        school_id = body.get("school_id")
        password = body.get("password")
    except:
        return JSONResponse(content={"error": "Invalid request format"}, status_code=400)
    
    if not school_id or not password:
        return JSONResponse(content={"error": "School ID and password are required"}, status_code=400)
    
    user = db.query(User).filter(User.school_id == school_id).first()
    if not user or not user.check_password(password):
        # SECURITY: Generic error message to prevent account enumeration
        return JSONResponse(content={"error": "Invalid School ID or password"}, status_code=401)
    
    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    if not access_token:
        return JSONResponse(content={"error": "Internal authentication error"}, status_code=500)
    
    # Build redirect URL based on user type
    is_user_admin = is_admin(user, db)
    redirect_url = "/admin" if is_user_admin else "/dashboard"
    
    response = JSONResponse(content={
        "success": True,
        "redirect": redirect_url,
        "is_admin": is_user_admin
    })
    
    # Set JWT cookie with secure flags
    from app.auth import COOKIE_NAME
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        max_age=3600, # 1 hour
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https", # Only require HTTPS if the request is HTTPS
        path="/"
    )
    
    return response

@router.post("/logout")
async def api_logout():
    """Clear authentication cookies"""
    from app.auth import COOKIE_NAME
    response = JSONResponse(content={"success": True, "redirect": "/"})
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return response

@router.post("/register")
async def api_register(request: Request, db: Session = Depends(get_db)):
    """Register a new student account (FormData)."""
    try:
        body = await request.form()
        name = (body.get("name") or "").strip()
        school_id = (body.get("school_id") or "").strip()
        password = body.get("password") or ""
    except Exception:
        return JSONResponse(content={"error": "Invalid request format"}, status_code=400)

    if not name or not school_id or not password:
        return JSONResponse(content={"error": "All fields are required"}, status_code=400)

    if school_id.lower() == "admin":
        return JSONResponse(content={"error": "School ID not allowed"}, status_code=400)

    existing = db.query(User).filter(User.school_id == school_id).first()
    if existing:
        return JSONResponse(content={"error": "School ID already exists"}, status_code=400)

    new_user = User(school_id=school_id, name=name)
    new_user.set_password(password)
    db.add(new_user)
    db.commit()

    return JSONResponse(content={"success": True})

@router.get("/posts")
async def get_posts(request: Request, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Eagerly load comments and author to avoid N+1 queries
    from sqlalchemy.orm import joinedload
    offset = (page - 1) * limit
    posts = db.query(Post).options(
        joinedload(Post.author),
        joinedload(Post.comments).joinedload(Comment.author)
    ).order_by(Post.timestamp.desc()).offset(offset).limit(limit).all()
    
    result = []
    for p in posts:
        # Use subqueries or optimized count for reactions
        reactions = {
            'like': db.query(Reaction).filter(Reaction.post_id == p.id, Reaction.type == 'like').count(),
            'love': db.query(Reaction).filter(Reaction.post_id == p.id, Reaction.type == 'love').count(),
            'wow': db.query(Reaction).filter(Reaction.post_id == p.id, Reaction.type == 'wow').count()
        }
        
        comments = [{
            "id": c.id,
            "content": c.content,
            "user": c.author.name,
            "timestamp": c.timestamp.isoformat()
        } for c in p.comments]
            
        result.append({
            "id": p.id,
            "content": p.content,
            "author": p.author.name,
            "timestamp": p.timestamp.isoformat(),
            "reactions": reactions,
            "comments": comments
        })
    return result

@router.post("/posts", response_model=PostResponse)
async def create_post(request: Request, post: PostCreate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    new_post = Post(user_id=user.id, content=post.content)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return {"id": new_post.id, "content": new_post.content, "author": user.name, "timestamp": new_post.timestamp}

@router.post("/posts/{post_id}/react")
async def react_to_post(post_id: int, reaction: ReactionCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if reaction exists
    existing = db.query(Reaction).filter(Reaction.post_id == post_id, Reaction.user_id == user.id).first()
    if existing:
        if existing.type == reaction.type:
            db.delete(existing)
        else:
            existing.type = reaction.type
    else:
        new_reaction = Reaction(post_id=post_id, user_id=user.id, type=reaction.type)
        db.add(new_reaction)
    
    db.commit()
    
    # Return updated counts
    counts = {}
    for r_type in ['like', 'love', 'wow']:
        counts[r_type] = db.query(Reaction).filter(Reaction.post_id == post_id, Reaction.type == r_type).count()
    
    return {"reactions": counts}

@router.post("/posts/{post_id}/comments")
async def add_comment(post_id: int, comment: CommentCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    new_comment = Comment(post_id=post_id, user_id=user.id, content=comment.content)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {
        "id": new_comment.id,
        "content": new_comment.content,
        "user": user.name,
        "timestamp": new_comment.timestamp.isoformat()
    }

@router.get("/grades", response_model=List[GradeResponse])
async def get_grades(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user.id).order_by(SubjectGrade.timestamp.desc()).all()
    return [{
        "id": g.id, "subject": g.subject, "units": g.units, "grade": g.grade, 
        "year": g.year, "semester": g.semester, "timestamp": g.timestamp, "failed": g.is_failed()
    } for g in grades]

@router.post("/grades", response_model=GradeResponse)
async def create_grade(request: Request, grade: GradeCreate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validation: grade must be between 1.0 and 5.0
    if grade.grade < 1.0 or grade.grade > 5.0:
        raise HTTPException(status_code=400, detail="Grade must be between 1.0 and 5.0")
    
    # Validation: units must be positive
    if grade.units <= 0:
        raise HTTPException(status_code=400, detail="Units must be greater than zero")
    
    # Clear cache for this user and global analytics
    compute_gwa_for_user.cache_clear()
    analyze_latin_honors.cache_clear()
    get_global_analytics.cache_clear()
    
    new_grade = SubjectGrade(
        user_id=user.id, subject=grade.subject, units=grade.units, 
        grade=grade.grade, year=grade.year, semester=grade.semester
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    
    # Return GWA in response for frontend update
    gwa = compute_gwa_for_user(user.id, db)
    
    return {
        "id": new_grade.id, "subject": new_grade.subject, "units": new_grade.units, 
        "grade": new_grade.grade, "year": new_grade.year, "semester": new_grade.semester, 
        "timestamp": new_grade.timestamp, "failed": new_grade.is_failed(),
        "gwa": gwa
    }

@router.get("/debug/students")
async def list_students_debug(db: Session = Depends(get_db)):
    students = db.query(User).filter(User.school_id != 'admin').limit(10).all()
    return [{"id": s.id, "name": s.name, "school_id": s.school_id} for s in students]

@router.get("/analytics")
async def get_analytics(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return get_global_analytics(db)

@router.get("/admin/students", response_model=List[dict])
async def get_students(request: Request, page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    offset = (page - 1) * limit
    students = db.query(User).filter(User.school_id != 'admin').offset(offset).limit(limit).all()
    
    result = []
    for u in students:
        # Use cached GWA
        gwa = compute_gwa_for_user(u.id, db)
        failed_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == u.id, SubjectGrade.grade > 3.0).count()
        result.append({
            "id": u.id,
            "school_id": u.school_id,
            "name": u.name,
            "department": u.department,
            "course": u.course,
            "gwa": gwa,
            "failed_count": failed_count
        })
    return result

@router.post("/admin/students", response_model=UserResponse)
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
    
    # Assign 8 default subjects to new student
    import random
    default_subjects = [
        "Data Structures and Algorithms", "Database Systems", "Operating Systems", 
        "Computer Organization", "Software Engineering", "Web Development", 
        "Artificial Intelligence", "Network Security"
    ]
    for subject in default_subjects:
        # Random grade between 1.0 and 3.0 (passing)
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
    
    return new_user

@router.get("/admin/student/{student_id}")
async def get_student_detail(student_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    gwa = compute_gwa_for_user(student.id, db)
    
    return {
        "id": student.id,
        "name": student.name,
        "school_id": student.school_id,
        "course": student.course,
        "department": student.department,
        "gwa": gwa,
        "posts": [{"id": p.id, "content": p.content} for p in student.posts],
        "grades": [{"id": g.id, "subject": g.subject, "grade": g.grade} for g in student.grades]
    }

@router.put("/admin/student/{student_id}", response_model=UserResponse)
async def update_student(student_id: int, student_update: UserUpdate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update fields if provided
    if student_update.name is not None:
        student.name = student_update.name
    if student_update.school_id is not None:
        # Check if new school ID is already taken by another user
        existing = db.query(User).filter(User.school_id == student_update.school_id, User.id != student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="School ID already exists")
        student.school_id = student_update.school_id
    if student_update.department is not None:
        student.department = student_update.department
    if student_update.course is not None:
        student.course = student_update.course
    if student_update.password is not None and student_update.password != "":
        student.set_password(student_update.password)
        
    db.commit()
    db.refresh(student)
    return student

@router.delete("/admin/student/{student_id}")
async def delete_student(student_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    try:
        db.delete(student)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/analytics/department_avg")
async def get_department_avg(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Calculate weighted GWA per department
    from sqlalchemy import func
    
    # Fetch all unique departments from the database
    departments = db.query(User.department).filter(User.department != None).distinct().all()
    dept_names = [d[0] for d in departments]
    
    result = {}
    
    for dept_name in dept_names:
        # Get users in this department
        users_in_dept = db.query(User.id).filter(User.department == dept_name).all()
        user_ids = [u.id for u in users_in_dept]
        
        if not user_ids:
            result[dept_name] = 0
            continue
            
        # Calculate weighted average GWA for the entire department
        # sum(units * grade) / sum(units)
        avg_gwa = db.query(
            func.sum(SubjectGrade.units * SubjectGrade.grade) / func.sum(SubjectGrade.units)
        ).filter(SubjectGrade.user_id.in_(user_ids), SubjectGrade.units > 0).scalar()
        
        result[dept_name] = round(float(avg_gwa), 3) if avg_gwa else 0
        
    return result

@router.get("/analytics/failure_rates")
async def get_failure_rates(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Calculate failure rates per department
    # Fetch all unique departments from the database
    departments = db.query(User.department).filter(User.department != None).distinct().all()
    dept_names = [d[0] for d in departments]
    
    result = {}
    
    for dept_name in dept_names:
        # Get users in this department
        users_in_dept = db.query(User.id).filter(User.department == dept_name).all()
        user_ids = [u.id for u in users_in_dept]
        
        if not user_ids:
            result[dept_name] = 0
            continue
            
        # Count total grades and failed grades (> 3.0)
        total_grades = db.query(SubjectGrade).filter(SubjectGrade.user_id.in_(user_ids)).count()
        if total_grades == 0:
            result[dept_name] = 0
            continue
            
        failed_grades = db.query(SubjectGrade).filter(
            SubjectGrade.user_id.in_(user_ids),
            SubjectGrade.grade > 3.0
        ).count()
        
        result[dept_name] = round((failed_grades / total_grades) * 100, 1)
        
    return result

@router.get("/analytics/user-timeline")
async def get_user_timeline(user_id: int, request: Request, db: Session = Depends(get_db)):
    """API for GWA Chart timeline for a specific user"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Permission check: admin or the user themselves
    if not is_admin(user, db) and user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user_id).order_by(SubjectGrade.timestamp.asc()).all()
    
    timeline = []
    running_total_units = 0
    running_total_points = 0
    
    for g in grades:
        if g.units is not None and g.grade is not None:
            running_total_units += g.units
            running_total_points += (g.units * g.grade)
            timeline.append({
                "timestamp": g.timestamp.isoformat(),
                "gwa": round(running_total_points / running_total_units, 3) if running_total_units > 0 else 0
            })
    
    return {"timeline": timeline}
