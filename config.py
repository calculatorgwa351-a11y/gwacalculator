import os
import ssl
import certifi
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    _pg_user = os.getenv("PGUSER")
    _pg_password = os.getenv("PGPASSWORD")
    _pg_host = os.getenv("PGHOST")
    _pg_port = os.getenv("PGPORT")
    _pg_db = os.getenv("PGDATABASE")
    _pg_ready = all([_pg_user, _pg_password, _pg_host, _pg_port, _pg_db])
    _pg_uri = (
        f"postgresql+pg8000://{_pg_user}:{_pg_password}@{_pg_host}:{_pg_port}/{_pg_db}"
        if _pg_ready
        else None
    )

    _raw_db_url = os.getenv("SQLALCHEMY_DATABASE_URI") or os.getenv("DATABASE_URL")
    if _raw_db_url:
        if _raw_db_url.startswith("postgres://"):
            _raw_db_url = _raw_db_url.replace("postgres://", "postgresql+pg8000://", 1)
        elif _raw_db_url.startswith("postgresql://") and "+pg8000" not in _raw_db_url:
            _raw_db_url = "postgresql+pg8000://" + _raw_db_url[len("postgresql://"):]

    SQLALCHEMY_DATABASE_URI = _raw_db_url or _pg_uri or "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {}
    if _pg_ready:
        _no_verify = os.getenv("SUPABASE_SSL_NO_VERIFY", "").lower() in ("1", "true", "yes")
        if _no_verify:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        else:
            ctx = ssl.create_default_context(cafile=certifi.where())
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"ssl_context": ctx}}

    DEBUG = os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "").lower() in (
        "1",
        "true",
        "yes",
    )
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME = 604800  # 7 days in seconds

    # CORS Settings
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")
