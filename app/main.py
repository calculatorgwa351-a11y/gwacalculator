import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url

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

BOOTSTRAP_LOCK_ID = 934_511_207


@dataclass
class BootstrapState:
    status: str = "pending"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


bootstrap_state = BootstrapState()
bootstrap_task: Optional[asyncio.Task] = None

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


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_bootstrap_state(
    *,
    status: str,
    started_at: Optional[str] = None,
    finished_at: Optional[str] = None,
    error: Optional[str] = None,
) -> None:
    bootstrap_state.status = status
    bootstrap_state.started_at = started_at
    bootstrap_state.finished_at = finished_at
    bootstrap_state.error = error


def _database_target() -> str:
    database_target = "unknown"
    try:
        parsed = make_url(settings.database_url)
        if settings.database_backend == "sqlite":
            database_target = parsed.database or "sqlite"
        else:
            host = parsed.host or ""
            database = parsed.database or ""
            database_target = f"{host}/{database}".strip("/") or settings.database_backend
    except Exception:
        database_target = settings.database_backend

    return database_target


@app.get("/api/health")
async def health_check():
    # For load balancer health checks, return OK immediately
    # Bootstrap status is available but doesn't block health checks
    return {
        "status": "ok",
        "environment": settings.app_env,
        "database_backend": settings.database_backend,
        "database_target": _database_target(),
        "bootstrap_status": bootstrap_state.status,
        "bootstrap_started_at": bootstrap_state.started_at,
        "bootstrap_finished_at": bootstrap_state.finished_at,
        "bootstrap_error": bootstrap_state.error,
    }


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

        if (
            admin_user
            and settings.reset_admin_password_on_startup
            and settings.default_admin_password
        ):
            admin_user.set_password(settings.default_admin_password)
            db.commit()
            logger.info("Reset bootstrap admin password for %s on startup.", admin_school_id)

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
            from init import reset_demo_student_passwords

            reset_count = reset_demo_student_passwords(db, school_id_prefix="2024", password="password123")
            if admin_user and settings.default_admin_password:
                admin_user.set_password(settings.default_admin_password)
                db.commit()
            logger.info("Reset demo passwords for %s students on startup.", reset_count)

        if settings.seed_demo_data:
            try:
                from init import ensure_grades_for_all_students, ensure_posts_for_all_students

                ensure_grades_for_all_students(db, min_subjects=8)
                ensure_posts_for_all_students(db, min_posts=1)
            except Exception:
                logger.exception("Failed to ensure demo grades/posts for students")

        logger.info("Database initialization complete.")
    except Exception:
        logger.exception("Database initialization failed")
        db.rollback()
        raise
    finally:
        db.close()


def run_lightweight_migrations():
    """
    Apply small, safe schema fixes for existing databases without full Alembic.
    """
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        if "comment" in table_names:
            comment_cols = {col["name"] for col in inspector.get_columns("comment")}
            if "parent_comment_id" not in comment_cols:
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE comment ADD COLUMN parent_comment_id INTEGER"))
                logger.info("Applied migration: added comment.parent_comment_id")

        index_statements = []
        if "subject_grade" in table_names:
            index_statements.extend(
                [
                    "CREATE INDEX IF NOT EXISTS ix_subject_grade_user_year_semester ON subject_grade (user_id, year, semester)",
                    "CREATE INDEX IF NOT EXISTS ix_subject_grade_user_grade ON subject_grade (user_id, grade)",
                ]
            )
        if "post" in table_names:
            index_statements.append("CREATE INDEX IF NOT EXISTS ix_post_user_timestamp ON post (user_id, timestamp)")
        if "comment" in table_names:
            index_statements.append("CREATE INDEX IF NOT EXISTS ix_comment_post_timestamp ON comment (post_id, timestamp)")
        if "reaction" in table_names:
            index_statements.append("CREATE INDEX IF NOT EXISTS ix_reaction_post_type ON reaction (post_id, type)")
        if "admin_audit" in table_names:
            index_statements.append("CREATE INDEX IF NOT EXISTS ix_admin_audit_user_timestamp ON admin_audit (admin_user_id, timestamp)")
        with engine.begin() as conn:
            for statement in index_statements:
                conn.execute(text(statement))
    except Exception:
        logger.exception("Lightweight migration step failed")


def _try_acquire_bootstrap_lock() -> bool:
    if settings.database_backend != "postgresql":
        return True

    with engine.connect() as conn:
        acquired = bool(
            conn.execute(
                text("SELECT pg_try_advisory_lock(:lock_id)"),
                {"lock_id": BOOTSTRAP_LOCK_ID},
            ).scalar()
        )

    if acquired:
        logger.info("Bootstrap advisory lock acquired.")
    else:
        logger.info("Bootstrap advisory lock already held by another worker; acting as follower.")
    return acquired


def _release_bootstrap_lock() -> None:
    if settings.database_backend != "postgresql":
        return

    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": BOOTSTRAP_LOCK_ID})


def _run_bootstrap_sequence() -> None:
    if not _try_acquire_bootstrap_lock():
        _set_bootstrap_state(
            status="ready",
            started_at=None,
            finished_at=_utc_now_iso(),
            error=None,
        )
        return

    started_at = _utc_now_iso()
    _set_bootstrap_state(status="running", started_at=started_at, finished_at=None, error=None)
    logger.info("Startup bootstrap started.")

    try:
        run_lightweight_migrations()
        init_database()
        run_lightweight_migrations()
    except Exception as exc:
        logger.exception("Startup bootstrap failed.")
        _set_bootstrap_state(
            status="failed",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            error=str(exc),
        )
        raise
    else:
        logger.info("Startup bootstrap completed.")
        _set_bootstrap_state(
            status="ready",
            started_at=started_at,
            finished_at=_utc_now_iso(),
            error=None,
        )
    finally:
        if settings.database_backend == "postgresql":
            try:
                _release_bootstrap_lock()
            except Exception:
                logger.exception("Failed to release bootstrap advisory lock.")


async def _run_bootstrap_in_background() -> None:
    try:
        await asyncio.to_thread(_run_bootstrap_sequence)
    except Exception:
        # State and logging are handled inside _run_bootstrap_sequence.
        return


@app.on_event("startup")
async def startup_event():
    global bootstrap_task

    logger.info("Application startup beginning.")
    logger.info("Database backend configured: %s (%s)", settings.database_backend, _database_target())
    _set_bootstrap_state(status="pending", started_at=None, finished_at=None, error=None)

    if settings.init_db_on_startup:
        if settings.startup_bootstrap_mode == "background":
            logger.info("Scheduling startup bootstrap in background mode.")
            bootstrap_task = asyncio.create_task(_run_bootstrap_in_background())
        else:
            logger.info("Running startup bootstrap in blocking mode.")
            try:
                _run_bootstrap_sequence()
            except Exception:
                if not settings.is_production:
                    raise
    else:
        logger.info("INIT_DB_ON_STARTUP is disabled; skipping startup DB bootstrap.")
        _set_bootstrap_state(
            status="ready",
            started_at=None,
            finished_at=_utc_now_iso(),
            error=None,
        )

    if not _dist_ready():
        logger.warning("Frontend dist/ bundle is missing; root path will return a deployment hint page.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=5000, reload=not settings.is_production)
