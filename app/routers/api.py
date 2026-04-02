from fastapi import APIRouter, Request, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import JSONResponse, Response, HTMLResponse
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import csv
import io
import json
from app.database import get_db
from app.auth import (
    COOKIE_NAME,
    create_access_token,
    get_cookie_settings,
    get_current_user,
    is_admin,
)
from app.models import User, Post, SubjectGrade, Admin, Reaction, Comment, AdminAudit
from app.schemas import (
    PostCreate, PostResponse, GradeCreate, GradeResponse, 
    ReactionCreate, CommentCreate, UserCreate, UserResponse, UserUpdate,
    ProfileUpdate, GradeUpdate, GradesBulkCreate, PostUpdate
)
from app.crud import compute_gwa_for_user, analyze_latin_honors, get_global_analytics

router = APIRouter(prefix="/api")

SUBJECT_TEMPLATES = {
    "COTE": {
        "Computer Science": [
            "Discrete Mathematics",
            "Data Structures and Algorithms",
            "Database Systems",
            "Operating Systems",
            "Computer Networks",
            "Software Engineering",
            "Web Development",
            "Artificial Intelligence",
        ],
        "Computer Engineering": [
            "Engineering Mathematics",
            "Digital Logic Design",
            "Computer Organization",
            "Microprocessors",
            "Data Structures and Algorithms",
            "Embedded Systems",
            "Network Security",
            "Software Engineering",
        ],
    },
    "COED": {
        "Elementary Education": [
            "Child and Adolescent Development",
            "Facilitating Learner-Centered Teaching",
            "Teaching Profession",
            "Assessment in Learning",
            "Educational Technology",
            "Curriculum Development",
            "Teaching Internship",
            "Field Study",
        ],
        "Secondary Education": [
            "Foundations of Education",
            "Teaching Profession",
            "Assessment in Learning",
            "Educational Technology",
            "Curriculum Development",
            "Teaching Methods",
            "Field Study",
            "Teaching Internship",
        ],
    },
    "CBM": {
        "Business Administration": [
            "Principles of Management",
            "Business Finance",
            "Marketing Management",
            "Operations Management",
            "Business Statistics",
            "Business Communication",
            "Strategic Management",
            "Entrepreneurship",
        ],
        "Accountancy": [
            "Financial Accounting",
            "Managerial Accounting",
            "Intermediate Accounting",
            "Auditing Principles",
            "Taxation",
            "Accounting Information Systems",
            "Business Law",
            "Cost Accounting",
        ],
    },
}

def _invalidate_analytics_caches():
    compute_gwa_for_user.cache_clear()
    analyze_latin_honors.cache_clear()
    get_global_analytics.cache_clear()

def _csv_response(filename: str, content: str) -> Response:
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _normalize_csv_row_keys(row: dict) -> dict:
    normalized = {}
    for key, value in row.items():
        normalized[(key or "").strip().lower()] = value
    return normalized

def _log_admin_action(
    db: Session,
    admin_user: User,
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    meta: Optional[dict] = None
):
    try:
        entry = AdminAudit(
            admin_user_id=admin_user.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            meta_json=json.dumps(meta or {})
        )
        db.add(entry)
        db.commit()
    except Exception:
        db.rollback()


def _require_admin_user(request: Request, db: Session) -> User:
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _serialize_grade(grade: SubjectGrade, gwa: Optional[float] = None) -> dict:
    return {
        "id": grade.id,
        "subject": grade.subject or "Untitled Subject",
        "units": float(grade.units) if grade.units is not None else 0.0,
        "grade": float(grade.grade) if grade.grade is not None else 0.0,
        "year": int(grade.year) if grade.year is not None else 1,
        "semester": int(grade.semester) if grade.semester is not None else 1,
        "timestamp": grade.timestamp.isoformat() if grade.timestamp else None,
        "failed": grade.is_failed(),
        "gwa": gwa,
    }


def _normalize_grade_payload(
    *,
    subject: Optional[str],
    units: Optional[float],
    grade_value: Optional[float],
    year: Optional[int],
    semester: Optional[int],
    allow_partial: bool = False,
) -> dict:
    payload: dict = {}

    if subject is not None:
        cleaned_subject = subject.strip()
        if not cleaned_subject:
            raise HTTPException(status_code=400, detail="Subject is required")
        payload["subject"] = cleaned_subject
    elif not allow_partial:
        raise HTTPException(status_code=400, detail="Subject is required")

    if units is not None:
        parsed_units = float(units)
        if parsed_units <= 0:
            raise HTTPException(status_code=400, detail="Units must be greater than zero")
        payload["units"] = parsed_units
    elif not allow_partial:
        raise HTTPException(status_code=400, detail="Units must be greater than zero")

    if grade_value is not None:
        parsed_grade = float(grade_value)
        if parsed_grade < 1.0 or parsed_grade > 5.0:
            raise HTTPException(status_code=400, detail="Grade must be between 1.0 and 5.0")
        payload["grade"] = parsed_grade
    elif not allow_partial:
        raise HTTPException(status_code=400, detail="Grade must be between 1.0 and 5.0")

    if year is not None:
        payload["year"] = int(year)
    elif not allow_partial:
        payload["year"] = 1

    if semester is not None:
        payload["semester"] = int(semester)
    elif not allow_partial:
        payload["semester"] = 1

    return payload


def _get_student_or_404(db: Session, student_id: int) -> User:
    student = db.query(User).filter(User.id == student_id, User.school_id != "admin").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

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

@router.put("/me")
async def update_me(payload: ProfileUpdate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if payload.name is not None and payload.name.strip() != "":
        user.name = payload.name.strip()
    if payload.department is not None:
        user.department = payload.department.strip() if payload.department else None
    if payload.course is not None:
        user.course = payload.course.strip() if payload.course else None
    if payload.password is not None and payload.password != "":
        user.set_password(payload.password)

    db.commit()
    db.refresh(user)

    return {
        "id": user.id,
        "school_id": user.school_id,
        "name": user.name,
        "department": user.department,
        "course": user.course,
        "is_admin": is_admin(user, db)
    }

@router.get("/subjects/templates")
async def get_subject_templates(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return {"templates": SUBJECT_TEMPLATES}

@router.get("/dashboard/summary")
async def get_dashboard_summary(request: Request, db: Session = Depends(get_db)):
    """Small summary payload for the student dashboard."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    gwa = compute_gwa_for_user(user.id, db)
    honors = analyze_latin_honors(user.id, db)

    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user.id).all()
    failed_count = sum(1 for g in grades if g.grade is not None and g.grade > 3.0)
    above_2_5_count = sum(1 for g in grades if g.grade is not None and g.grade > 2.5)

    # Next target (lower GWA is better)
    thresholds = [
        ("Summa Cum Laude", 1.20),
        ("Magna Cum Laude", 1.45),
        ("Cum Laude", 1.75)
    ]

    next_target = None
    gap_to_next = None
    if gwa is not None:
        # If already eligible for a title, the next target is the next stricter threshold.
        if honors.get("eligible") and honors.get("title"):
            if honors["title"] == "Cum Laude":
                next_target = "Magna Cum Laude"
                gap_to_next = round(max(0.0, gwa - 1.45), 3)
            elif honors["title"] == "Magna Cum Laude":
                next_target = "Summa Cum Laude"
                gap_to_next = round(max(0.0, gwa - 1.20), 3)
            else:
                next_target = None
                gap_to_next = 0.0
        else:
            # Not eligible yet: aim for Cum Laude threshold by default.
            next_target = "Cum Laude"
            gap_to_next = round(max(0.0, gwa - 1.75), 3)

    grade_count = len(grades)
    post_count = db.query(Post).filter(Post.user_id == user.id).count()

    return {
        "gwa": gwa,
        "honors": honors,
        "honors_progress": {
            "next_target": next_target,
            "gap_to_next_target": gap_to_next,
            "failed_count": failed_count,
            "above_2_5_count": above_2_5_count
        },
        "grade_count": grade_count,
        "post_count": post_count
    }

@router.post("/login")
async def api_login(request: Request, db: Session = Depends(get_db)):
    """AJAX/API login endpoint - accepts form or JSON and returns JSON."""
    try:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            body = await request.json()
            school_id = (body.get("school_id") or "").strip()
            password = body.get("password") or ""
        else:
            body = await request.form()
            school_id = (body.get("school_id") or "").strip()
            password = body.get("password") or ""
    except Exception:
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
    
    cookie_settings = get_cookie_settings(request)
    cookie_domain = cookie_settings.pop("domain")
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        domain=cookie_domain,
        **cookie_settings,
    )
    
    return response

@router.post("/logout")
async def api_logout():
    """Clear authentication cookies"""
    response = JSONResponse(content={"success": True, "redirect": "/"})
    cookie_settings = get_cookie_settings()
    response.delete_cookie(
        key=COOKIE_NAME,
        path=cookie_settings["path"],
        domain=cookie_settings.get("domain"),
    )
    return response

@router.post("/register")
async def api_register(request: Request, db: Session = Depends(get_db)):
    """Student self-registration is disabled. Admins create student accounts."""
    return JSONResponse(
        content={"error": "Student self-registration is disabled. Please contact the admin."},
        status_code=403,
    )

@router.get("/posts")
async def get_posts(request: Request, page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Eagerly load comments and author to avoid N+1 queries
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
            "user_id": c.user_id,
            "parent_comment_id": c.parent_comment_id,
            "timestamp": c.timestamp.isoformat(),
            "can_delete": (c.user_id == user.id) or is_admin(user, db)
        } for c in sorted(p.comments, key=lambda x: x.timestamp)]
            
        result.append({
            "id": p.id,
            "content": p.content,
            "author": p.author.name,
            "author_id": p.user_id,
            "timestamp": p.timestamp.isoformat(),
            "reactions": reactions,
            "comments": comments,
            "can_edit": (p.user_id == user.id) or is_admin(user, db)
        })
    return result

@router.get("/posts/feed")
async def get_posts_feed(
    request: Request,
    page: int = 1,
    limit: int = 10,
    department: Optional[str] = None,
    course: Optional[str] = None,
    mine: bool = False,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    limit = max(1, min(50, limit))
    page = max(1, page)
    offset = (page - 1) * limit

    q = db.query(Post).options(
        joinedload(Post.author),
        joinedload(Post.comments).joinedload(Comment.author)
    )

    if mine:
        q = q.filter(Post.user_id == user.id)

    if department or course:
        q = q.join(User, Post.user_id == User.id)
        if department:
            q = q.filter(User.department == department)
        if course:
            q = q.filter(User.course == course)

    total = q.count()
    posts = q.order_by(Post.timestamp.desc()).offset(offset).limit(limit).all()

    items = []
    for p in posts:
        reactions = {
            'like': db.query(Reaction).filter(Reaction.post_id == p.id, Reaction.type == 'like').count(),
            'love': db.query(Reaction).filter(Reaction.post_id == p.id, Reaction.type == 'love').count(),
            'wow': db.query(Reaction).filter(Reaction.post_id == p.id, Reaction.type == 'wow').count()
        }

        comments = [{
            "id": c.id,
            "content": c.content,
            "user": c.author.name,
            "user_id": c.user_id,
            "parent_comment_id": c.parent_comment_id,
            "timestamp": c.timestamp.isoformat(),
            "can_delete": (c.user_id == user.id) or is_admin(user, db)
        } for c in sorted(p.comments, key=lambda x: x.timestamp)]

        items.append({
            "id": p.id,
            "content": p.content,
            "author": p.author.name,
            "author_id": p.user_id,
            "department": p.author.department,
            "course": p.author.course,
            "timestamp": p.timestamp.isoformat(),
            "reactions": reactions,
            "comments": comments,
            "can_edit": (p.user_id == user.id) or is_admin(user, db)
        })

    return {"items": items, "page": page, "limit": limit, "total": total}

@router.put("/posts/{post_id}")
async def update_post(post_id: int, payload: PostUpdate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id and not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Forbidden")

    content = (payload.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    post.content = content
    db.commit()
    db.refresh(post)

    return {"success": True, "id": post.id, "content": post.content, "timestamp": post.timestamp.isoformat()}

@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if post.user_id != user.id and not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(post)
    db.commit()
    return {"success": True}

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
    
    parent_id = comment.parent_id
    if parent_id is not None:
        parent = db.query(Comment).filter(Comment.id == parent_id, Comment.post_id == post_id).first()
        if not parent:
            raise HTTPException(status_code=400, detail="Invalid parent comment")

    new_comment = Comment(
        post_id=post_id,
        user_id=user.id,
        parent_comment_id=parent_id,
        content=comment.content
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return {
        "id": new_comment.id,
        "content": new_comment.content,
        "parent_comment_id": new_comment.parent_comment_id,
        "user_id": user.id,
        "user": user.name,
        "timestamp": new_comment.timestamp.isoformat()
    }

@router.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    comment = db.query(Comment).filter(Comment.id == comment_id, Comment.post_id == post_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.user_id != user.id and not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(comment)
    db.commit()
    return {"success": True}

@router.get("/grades", response_model=List[GradeResponse])
async def get_grades(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    grades = db.query(SubjectGrade).filter(SubjectGrade.user_id == user.id).order_by(SubjectGrade.timestamp.desc()).all()
    return [_serialize_grade(g) for g in grades]

@router.post("/grades", response_model=GradeResponse)
async def create_grade(request: Request, grade: GradeCreate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    raise HTTPException(status_code=403, detail="Grade management is admin-only")

@router.put("/grades/{grade_id}", response_model=GradeResponse)
async def update_grade(grade_id: int, request: Request, payload: GradeUpdate, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    raise HTTPException(status_code=403, detail="Grade management is admin-only")

@router.delete("/grades/{grade_id}")
async def delete_grade(grade_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    raise HTTPException(status_code=403, detail="Grade management is admin-only")

@router.post("/grades/bulk")
async def bulk_create_grades(payload: GradesBulkCreate, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    raise HTTPException(status_code=403, detail="Grade management is admin-only")

@router.get("/grades/export.csv")
async def export_grades_csv(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    raise HTTPException(status_code=403, detail="Grade management is admin-only")

@router.post("/grades/import")
async def import_grades_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    raise HTTPException(status_code=403, detail="Grade management is admin-only")


@router.get("/admin/student/{student_id}/grades", response_model=List[GradeResponse])
async def admin_get_student_grades(student_id: int, request: Request, db: Session = Depends(get_db)):
    _require_admin_user(request, db)
    student = _get_student_or_404(db, student_id)
    grades = (
        db.query(SubjectGrade)
        .filter(SubjectGrade.user_id == student.id)
        .order_by(SubjectGrade.year.asc(), SubjectGrade.semester.asc(), SubjectGrade.subject.asc(), SubjectGrade.timestamp.desc())
        .all()
    )
    gwa = compute_gwa_for_user(student.id, db)
    return [_serialize_grade(grade, gwa) for grade in grades]


@router.post("/admin/student/{student_id}/grades", response_model=GradeResponse)
async def admin_create_student_grade(
    student_id: int,
    grade: GradeCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    admin_user = _require_admin_user(request, db)
    student = _get_student_or_404(db, student_id)
    normalized = _normalize_grade_payload(
        subject=grade.subject,
        units=grade.units,
        grade_value=grade.grade,
        year=grade.year,
        semester=grade.semester,
    )

    new_grade = SubjectGrade(user_id=student.id, **normalized)
    db.add(new_grade)
    _invalidate_analytics_caches()
    db.commit()
    db.refresh(new_grade)

    gwa = compute_gwa_for_user(student.id, db)
    _log_admin_action(
        db,
        admin_user,
        action="grade_create",
        target_type="user",
        target_id=student.id,
        meta={"school_id": student.school_id, "grade_id": new_grade.id, "subject": new_grade.subject},
    )
    return _serialize_grade(new_grade, gwa)


@router.put("/admin/student/{student_id}/grades/{grade_id}", response_model=GradeResponse)
async def admin_update_student_grade(
    student_id: int,
    grade_id: int,
    payload: GradeUpdate,
    request: Request,
    db: Session = Depends(get_db),
):
    admin_user = _require_admin_user(request, db)
    student = _get_student_or_404(db, student_id)
    grade = db.query(SubjectGrade).filter(SubjectGrade.id == grade_id, SubjectGrade.user_id == student.id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    normalized = _normalize_grade_payload(
        subject=payload.subject,
        units=payload.units,
        grade_value=payload.grade,
        year=payload.year,
        semester=payload.semester,
        allow_partial=True,
    )

    for key, value in normalized.items():
        setattr(grade, key, value)

    _invalidate_analytics_caches()
    db.commit()
    db.refresh(grade)

    gwa = compute_gwa_for_user(student.id, db)
    _log_admin_action(
        db,
        admin_user,
        action="grade_update",
        target_type="user",
        target_id=student.id,
        meta={"school_id": student.school_id, "grade_id": grade.id, "subject": grade.subject},
    )
    return _serialize_grade(grade, gwa)


@router.delete("/admin/student/{student_id}/grades/{grade_id}")
async def admin_delete_student_grade(student_id: int, grade_id: int, request: Request, db: Session = Depends(get_db)):
    admin_user = _require_admin_user(request, db)
    student = _get_student_or_404(db, student_id)
    grade = db.query(SubjectGrade).filter(SubjectGrade.id == grade_id, SubjectGrade.user_id == student.id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")

    subject = grade.subject
    db.delete(grade)
    _invalidate_analytics_caches()
    db.commit()

    gwa = compute_gwa_for_user(student.id, db)
    _log_admin_action(
        db,
        admin_user,
        action="grade_delete",
        target_type="user",
        target_id=student.id,
        meta={"school_id": student.school_id, "grade_id": grade_id, "subject": subject},
    )
    return {"success": True, "gwa": gwa}


@router.get("/admin/grades/import-template.csv")
async def admin_grade_import_template(request: Request, db: Session = Depends(get_db)):
    _require_admin_user(request, db)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["school_id", "subject", "units", "grade", "year", "semester", "id"])

    students = (
        db.query(User)
        .filter(User.school_id != "admin")
        .order_by(User.school_id.asc())
        .all()
    )

    if not students:
        writer.writerow(["20240001", "Data Structures and Algorithms", "3", "1.75", "1", "1", ""])
        return _csv_response("grades_import_template.csv", output.getvalue())

    student_ids = [student.id for student in students]
    grades = (
        db.query(SubjectGrade)
        .filter(SubjectGrade.user_id.in_(student_ids))
        .order_by(
            SubjectGrade.user_id.asc(),
            SubjectGrade.year.asc(),
            SubjectGrade.semester.asc(),
            SubjectGrade.subject.asc(),
        )
        .all()
        if student_ids
        else []
    )

    grades_by_student: dict[int, list[SubjectGrade]] = {student.id: [] for student in students}
    for grade in grades:
        grades_by_student.setdefault(grade.user_id, []).append(grade)

    for student in students:
        student_grades = grades_by_student.get(student.id, [])
        if student_grades:
            for grade in student_grades:
                writer.writerow(
                    [
                        student.school_id,
                        grade.subject,
                        grade.units,
                        grade.grade,
                        grade.year,
                        grade.semester,
                        grade.id,
                    ]
                )
        else:
            writer.writerow([student.school_id, "", "", "", "", "", ""])

    return _csv_response("grades_import_template.csv", output.getvalue())


@router.post("/admin/grades/import")
async def admin_import_grades_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    admin_user = _require_admin_user(request, db)

    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8-sig")
    except Exception:
        text = raw.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    required = {"school_id", "subject", "units", "grade", "year", "semester"}
    fieldnames = {(field or "").strip().lower() for field in (reader.fieldnames or [])}
    if not reader.fieldnames or not required.issubset(fieldnames):
        raise HTTPException(
            status_code=400,
            detail="CSV must include: school_id, subject, units, grade, year, semester (optional: id)",
        )

    rows = list(reader)
    errors = []
    normalized_rows = []

    for line_number, row in enumerate(rows, start=2):
        try:
            normalized_row = _normalize_csv_row_keys(row)
            school_id = (normalized_row.get("school_id") or "").strip()
            if not school_id:
                raise ValueError("school_id is required")

            student = db.query(User).filter(User.school_id == school_id, User.school_id != "admin").first()
            if not student:
                raise ValueError(f"unknown school_id: {school_id}")

            normalized = _normalize_grade_payload(
                subject=normalized_row.get("subject"),
                units=float(normalized_row.get("units") or 0),
                grade_value=float(normalized_row.get("grade") or 0),
                year=int(float(normalized_row.get("year") or 1)),
                semester=int(float(normalized_row.get("semester") or 1)),
            )

            raw_id = (normalized_row.get("id") or "").strip()
            target = None
            if raw_id:
                try:
                    grade_id = int(float(raw_id))
                except Exception as exc:
                    raise ValueError(f"invalid id: {raw_id}") from exc

                target = db.query(SubjectGrade).filter(SubjectGrade.id == grade_id).first()
                if not target:
                    raise ValueError(f"grade id not found: {grade_id}")
                if target.user_id != student.id:
                    raise ValueError(f"grade id {grade_id} does not belong to school_id {school_id}")

            normalized_rows.append(
                {
                    "line": line_number,
                    "school_id": school_id,
                    "student": student,
                    "target": target,
                    **normalized,
                }
            )
        except HTTPException as exc:
            errors.append({"line": line_number, "error": exc.detail})
        except Exception as exc:
            errors.append({"line": line_number, "error": str(exc)})

    if errors:
        return JSONResponse(content={"success": False, "inserted": 0, "updated": 0, "errors": errors}, status_code=400)

    inserted = 0
    updated = 0
    affected_school_ids = set()
    try:
        for item in normalized_rows:
            target = item["target"]
            student = item["student"]
            affected_school_ids.add(student.school_id)
            if target is None:
                target = (
                    db.query(SubjectGrade)
                    .filter(
                        SubjectGrade.user_id == student.id,
                        SubjectGrade.subject == item["subject"],
                        SubjectGrade.year == item["year"],
                        SubjectGrade.semester == item["semester"],
                    )
                    .first()
                )

            if target:
                target.subject = item["subject"]
                target.units = item["units"]
                target.grade = item["grade"]
                target.year = item["year"]
                target.semester = item["semester"]
                updated += 1
            else:
                db.add(
                    SubjectGrade(
                        user_id=student.id,
                        subject=item["subject"],
                        units=item["units"],
                        grade=item["grade"],
                        year=item["year"],
                        semester=item["semester"],
                    )
                )
                inserted += 1

        _invalidate_analytics_caches()
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Import failed: {exc}")

    result = {
        "inserted": inserted,
        "updated": updated,
        "students_affected": len(affected_school_ids),
        "errors": [],
    }
    _log_admin_action(db, admin_user, action="grade_import", meta=result)
    return {"success": True, **result}

@router.get("/analytics/semester_gwa")
async def get_semester_gwa(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    grades = (
        db.query(SubjectGrade)
        .filter(SubjectGrade.user_id == user.id)
        .order_by(SubjectGrade.year.asc(), SubjectGrade.semester.asc(), SubjectGrade.timestamp.asc())
        .all()
    )

    buckets = {}
    for g in grades:
        if g.units is None or g.grade is None:
            continue

        subj_upper = (g.subject or "").upper()
        if "NSTP" in subj_upper or "ROTC" in subj_upper:
            continue

        key = (int(g.year or 1), int(g.semester or 1))
        if key not in buckets:
            buckets[key] = {"points": 0.0, "units": 0.0}
        buckets[key]["points"] += float(g.units) * float(g.grade)
        buckets[key]["units"] += float(g.units)

    series = []
    for (year, semester) in sorted(buckets.keys()):
        units = buckets[(year, semester)]["units"]
        points = buckets[(year, semester)]["points"]
        series.append({"year": year, "semester": semester, "gwa": round(points / units, 3) if units > 0 else None})

    return {"items": series}

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
    _log_admin_action(
        db,
        user,
        action="student_create",
        target_type="user",
        target_id=new_user.id,
        meta={"school_id": new_user.school_id},
    )
    
    return new_user

@router.post("/admin/seed/filipino_names")
async def seed_filipino_names(request: Request, db: Session = Depends(get_db)):
    """Admin-only: rename dummy students (e.g. 2024xxxx) to Filipino-style names."""
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from init import assign_filipino_names_to_students
        updated = assign_filipino_names_to_students(db, school_id_prefix="2024")
        _log_admin_action(db, user, action="seed_filipino_names", meta={"updated": updated})
        return {"success": True, "updated": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed names: {e}")

@router.post("/admin/seed/demo_data")
async def seed_demo_data(
    request: Request,
    student_count: int = Query(default=12, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Admin-only: add missing demo students/data without deleting existing users."""
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from init import (
            assign_filipino_names_to_students,
            ensure_grades_for_all_students,
            ensure_posts_for_all_students,
            generate_dummy_data,
        )

        seed_result = generate_dummy_data(db, student_count=student_count, add_if_existing=True)
        seeded_grades = ensure_grades_for_all_students(db, min_subjects=8)
        post_result = ensure_posts_for_all_students(db, min_posts=1)
        renamed_students = assign_filipino_names_to_students(db, school_id_prefix="2024")

        _invalidate_analytics_caches()
        result = {
            "created_students": int(seed_result.get("created_students", 0)),
            "existing_students": int(seed_result.get("existing_students", 0)),
            "seeded_grades": int(seed_result.get("seeded_grades", 0)) + seeded_grades,
            "seeded_posts": int(seed_result.get("seeded_posts", 0)) + int(post_result.get("seeded_posts", 0)),
            "seeded_comments": int(seed_result.get("seeded_comments", 0)) + int(post_result.get("seeded_comments", 0)),
            "renamed_students": renamed_students,
            "skipped_existing_demo": int(seed_result.get("skipped_existing_demo", 0)),
        }
        _log_admin_action(db, user, action="seed_demo_data", meta=result)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to seed demo data: {e}")

@router.post("/admin/student/{student_id}/reset_password")
async def admin_reset_student_password(student_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    student = db.query(User).filter(User.id == student_id, User.school_id != "admin").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    import secrets

    new_password = secrets.token_urlsafe(8)
    student.set_password(new_password)
    db.commit()

    _log_admin_action(
        db,
        user,
        action="student_reset_password",
        target_type="user",
        target_id=student.id,
        meta={"school_id": student.school_id},
    )

    return {"success": True, "student_id": student.id, "school_id": student.school_id, "password": new_password}

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
        "grades": [{
            "id": g.id,
            "subject": g.subject or "Untitled Subject",
            "units": float(g.units) if g.units is not None else 0.0,
            "grade": float(g.grade) if g.grade is not None else 0.0,
            "year": int(g.year) if g.year is not None else 1,
            "semester": int(g.semester) if g.semester is not None else 1,
            "timestamp": g.timestamp.isoformat() if g.timestamp else None,
            "failed": g.is_failed()
        } for g in student.grades]
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
    _log_admin_action(db, user, action="student_update", target_type="user", target_id=student.id)
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
        _log_admin_action(db, user, action="student_delete", target_type="user", target_id=student_id)
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/admin/audit")
async def get_admin_audit(request: Request, page: int = 1, limit: int = 20, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    limit = max(1, min(50, limit))
    page = max(1, page)
    offset = (page - 1) * limit

    q = db.query(AdminAudit).options(joinedload(AdminAudit.admin_user)).order_by(AdminAudit.timestamp.desc())
    total = q.count()
    items = q.offset(offset).limit(limit).all()

    return {
        "items": [
            {
                "id": a.id,
                "admin_user_id": a.admin_user_id,
                "admin_name": a.admin_user.name if a.admin_user else None,
                "action": a.action,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "meta": json.loads(a.meta_json) if a.meta_json else {},
                "timestamp": a.timestamp.isoformat() if a.timestamp else None,
            }
            for a in items
        ],
        "page": page,
        "limit": limit,
        "total": total,
    }

@router.get("/admin/reports/students.csv")
async def admin_report_students_csv(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    students = db.query(User).filter(User.school_id != "admin").order_by(User.school_id.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["school_id", "name", "department", "course", "gwa", "failed_count", "honors_title", "honors_eligible"])

    for s in students:
        gwa = compute_gwa_for_user(s.id, db)
        failed_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == s.id, SubjectGrade.grade > 3.0).count()
        honors = analyze_latin_honors(s.id, db)
        writer.writerow(
            [
                s.school_id,
                s.name,
                s.department or "",
                s.course or "",
                f"{gwa:.3f}" if gwa is not None else "",
                failed_count,
                honors.get("title") or "",
                "yes" if honors.get("eligible") else "no",
            ]
        )

    _log_admin_action(db, user, action="report_students_csv")
    return _csv_response("students_report.csv", output.getvalue())

@router.get("/admin/reports/student/{student_id}.html")
async def admin_report_student_html(student_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    student = db.query(User).filter(User.id == student_id, User.school_id != "admin").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    gwa = compute_gwa_for_user(student.id, db)
    honors = analyze_latin_honors(student.id, db)
    failed_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == student.id, SubjectGrade.grade > 3.0).count()
    grades = (
        db.query(SubjectGrade)
        .filter(SubjectGrade.user_id == student.id)
        .order_by(SubjectGrade.year.asc(), SubjectGrade.semester.asc(), SubjectGrade.subject.asc())
        .all()
    )

    def esc(s: str) -> str:
        return (
            str(s)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    rows = "\n".join(
        f"<tr><td>{esc(g.subject)}</td><td>{g.units:.1f}</td><td>{g.grade:.2f}</td><td>{g.year}</td><td>{g.semester}</td></tr>"
        for g in grades
    )

    html = f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Student Report - {esc(student.school_id)}</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; padding: 32px; color: #0f172a; }}
    h1 {{ font-size: 22px; margin: 0; }}
    .muted {{ color: #64748b; font-size: 12px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 16px; }}
    .card {{ border: 1px solid #e2e8f0; border-radius: 16px; padding: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 10px 8px; text-align: left; font-size: 12px; }}
    th {{ background: #f8fafc; text-transform: uppercase; letter-spacing: .12em; font-size: 10px; color: #64748b; }}
    @media print {{ body {{ padding: 0; }} .card {{ break-inside: avoid; }} }}
  </style>
</head>
<body>
  <div class="muted">GWA Calculator | Printable Student Report</div>
  <h1>{esc(student.name)} <span class="muted">({esc(student.school_id)})</span></h1>
  <div class="muted">{esc(student.department or "-")} | {esc(student.course or "-")}</div>

  <div class="grid">
    <div class="card">
      <div class="muted">Current GWA</div>
      <div style="font-size:28px; font-weight:900; margin-top:6px;">{f"{gwa:.3f}" if gwa is not None else "-"}</div>
    </div>
    <div class="card">
      <div class="muted">Honors</div>
      <div style="font-size:16px; font-weight:900; margin-top:6px;">{esc(honors.get("title") or "Not eligible")}</div>
      <div class="muted" style="margin-top:4px;">{esc(honors.get("reason") or "")}</div>
      <div class="muted" style="margin-top:6px;">Failed grades: {failed_count}</div>
    </div>
  </div>

  <div class="card" style="margin-top:16px;">
    <div class="muted">Grades</div>
    <table>
      <thead><tr><th>Subject</th><th>Units</th><th>Grade</th><th>Year</th><th>Sem</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</body>
</html>
""".strip()

    _log_admin_action(db, user, action="report_student_html", target_type="user", target_id=student.id)
    return HTMLResponse(content=html)

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

@router.get("/analytics/grade_distribution")
async def get_grade_distribution(request: Request, db: Session = Depends(get_db)):
    """Admin-only grade distribution (histogram) across all students."""
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Exclude the admin user from analysis.
    student_ids = [u.id for u in db.query(User.id).filter(User.school_id != 'admin').all()]
    if not student_ids:
        return {"buckets": [], "total": 0}

    grades = db.query(SubjectGrade.grade).filter(SubjectGrade.user_id.in_(student_ids)).all()
    values = [g[0] for g in grades if g[0] is not None]

    buckets = [
        {"label": "1.00-1.25", "min": 1.0, "max": 1.25, "count": 0},
        {"label": "1.26-1.50", "min": 1.26, "max": 1.50, "count": 0},
        {"label": "1.51-1.75", "min": 1.51, "max": 1.75, "count": 0},
        {"label": "1.76-2.00", "min": 1.76, "max": 2.00, "count": 0},
        {"label": "2.01-2.50", "min": 2.01, "max": 2.50, "count": 0},
        {"label": "2.51-3.00", "min": 2.51, "max": 3.00, "count": 0},
        {"label": "3.01-5.00", "min": 3.01, "max": 5.00, "count": 0}
    ]

    for v in values:
        for b in buckets:
            if b["min"] <= v <= b["max"]:
                b["count"] += 1
                break

    return {"buckets": [{"label": b["label"], "count": b["count"]} for b in buckets], "total": len(values)}

@router.get("/analytics/top_bottom")
async def get_top_bottom(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    students = db.query(User).filter(User.school_id != "admin").all()
    scored = []
    for s in students:
        gwa = compute_gwa_for_user(s.id, db)
        if gwa is None:
            continue
        scored.append({"id": s.id, "school_id": s.school_id, "name": s.name, "gwa": gwa})

    scored.sort(key=lambda x: x["gwa"])
    top = scored[:5]
    bottom = list(reversed(scored[-5:])) if scored else []

    return {"top": top, "bottom": bottom}

@router.get("/analytics/at_risk")
async def get_at_risk(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or not is_admin(user, db):
        raise HTTPException(status_code=403, detail="Admin access required")

    students = db.query(User).filter(User.school_id != "admin").all()
    results = []

    for s in students:
        gwa = compute_gwa_for_user(s.id, db)
        failed_count = db.query(SubjectGrade).filter(SubjectGrade.user_id == s.id, SubjectGrade.grade > 3.0).count()
        reasons = []
        if gwa is None:
            reasons.append("No grades")
        if failed_count > 0:
            reasons.append("Has failing grades")
        if gwa is not None and gwa > 2.5:
            reasons.append("GWA above 2.50")

        if reasons:
            results.append(
                {
                    "id": s.id,
                    "school_id": s.school_id,
                    "name": s.name,
                    "department": s.department,
                    "course": s.course,
                    "gwa": gwa,
                    "failed_count": failed_count,
                    "reasons": reasons,
                }
            )

    results.sort(key=lambda x: (x["gwa"] is None, x["gwa"] or 99))
    return {"items": results}

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
