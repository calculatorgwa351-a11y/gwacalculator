import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Admin, Course, Department, User
from app.routers import api

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GWA Calculator",
    version="2.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

allow_credentials = settings.cors_allow_credentials and "*" not in settings.cors_allowed_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)


@app.middleware("http")
async def security_headers_middleware(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if settings.is_production and request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app.include_router(api.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "environment": settings.app_env}


DIST_DIR = Path("dist")


def _dist_ready() -> bool:
    return DIST_DIR.exists() and (DIST_DIR / "index.html").is_file()


def _frontend_missing_response() -> HTMLResponse:
    return HTMLResponse(
        content=(
            "<!doctype html><html><head><meta charset='utf-8'/>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'/>"
            "<title>GWA Calculator</title>"
            "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;margin:32px;color:#0f172a}"
            ".box{max-width:760px;border:1px solid #e2e8f0;border-radius:12px;padding:20px;background:#f8fafc}"
            "code{background:#e2e8f0;padding:2px 6px;border-radius:6px}</style></head><body>"
            "<div class='box'><h2>Frontend bundle not found</h2>"
            "<p>The API is running, but the SPA build files are missing.</p>"
            "<p>Deploy using Docker (recommended) or run <code>npm run build-only</code> so <code>dist/</code> exists.</p>"
            "<p>Health endpoint: <a href='/api/health'>/api/health</a></p></div></body></html>"
        ),
        status_code=503,
    )


@app.get("/")
async def serve_index():
    if not _dist_ready():
        return _frontend_missing_response()
    return FileResponse(DIST_DIR / "index.html")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404)
    if full_path in {"openapi.json", "docs", "redoc"}:
        raise HTTPException(status_code=404)

    if not _dist_ready():
        return _frontend_missing_response()

    candidate = DIST_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    return FileResponse(DIST_DIR / "index.html")


def init_database():
    """Initialize schema and optional bootstrap/demo records."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        departments_data = [
            {"name": "COTE", "courses": ["Computer Science", "Computer Engineering"]},
            {"name": "COED", "courses": ["Elementary Education", "Secondary Education"]},
            {"name": "CBM", "courses": ["Business Administration", "Accountancy"]},
        ]

        for dept_data in departments_data:
            dept = db.query(Department).filter(Department.name == dept_data["name"]).first()
            if not dept:
                dept = Department(name=dept_data["name"])
                db.add(dept)
                db.commit()
                logger.info("Created department %s", dept.name)

            for course_name in dept_data["courses"]:
                course = (
                    db.query(Course)
                    .filter(Course.name == course_name, Course.department_id == dept.id)
                    .first()
                )
                if not course:
                    course = Course(name=course_name, department_id=dept.id)
                    db.add(course)
                    db.commit()
                    logger.info("Created course %s under %s", course_name, dept.name)

        admin_school_id = settings.default_admin_school_id
        admin_user = db.query(User).filter(User.school_id == admin_school_id).first()
        if not admin_user:
            if settings.default_admin_password:
                admin_user = User(
                    school_id=admin_school_id,
                    name=settings.default_admin_name,
                    department="COTE",
                    course="Administration",
                )
                admin_user.set_password(settings.default_admin_password)
                db.add(admin_user)
                db.commit()
                logger.info("Created bootstrap admin user %s", admin_school_id)
            else:
                logger.warning(
                    "Admin user does not exist and DEFAULT_ADMIN_PASSWORD is empty; "
                    "skipping bootstrap admin creation."
                )

        if admin_user and not admin_user.name:
            admin_user.name = settings.default_admin_name
            db.commit()

        if admin_user:
            admin_record = db.query(Admin).filter(Admin.user_id == admin_user.id).first()
            if not admin_record:
                db.add(Admin(user_id=admin_user.id))
                db.commit()
                logger.info("Granted admin rights to %s", admin_school_id)

        student_count = db.query(User).filter(User.school_id != admin_school_id).count()
        if settings.seed_demo_data:
            try:
                from init import generate_dummy_data

                seed_result = generate_dummy_data(db, student_count=12, add_if_existing=True)
                created_students = int(seed_result.get("created_students", 0))
                if created_students > 0:
                    logger.info("Generated %s demo students.", created_students)
            except Exception:
                logger.exception("Failed to generate dummy data")
        elif student_count == 0:
            logger.info("No students found; demo seeding disabled.")

        if settings.reset_demo_passwords:
            users = db.query(User).all()
            for user in users:
                password = settings.default_admin_password if user.school_id == admin_school_id else "password123"
                if password:
                    user.set_password(password)
            db.commit()
            logger.info("Reset passwords for %s users (demo mode).", len(users))

        if settings.seed_demo_data:
            try:
                from init import ensure_grades_for_all_students

                ensure_grades_for_all_students(db, min_subjects=8)
            except Exception:
                logger.exception("Failed to ensure demo grades for students")

        logger.info("Database initialization complete.")
    except Exception:
        logger.exception("Database initialization failed")
        db.rollback()
        raise
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    if settings.init_db_on_startup:
        try:
            init_database()
        except Exception:
            logger.exception("Startup DB initialization failed.")
            if not settings.is_production:
                raise
    else:
        logger.info("INIT_DB_ON_STARTUP is disabled; skipping startup DB initialization.")
    if not _dist_ready():
        logger.warning("Frontend dist/ bundle is missing; root path will return a deployment hint page.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=not settings.is_production)
