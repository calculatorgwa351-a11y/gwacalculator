from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv(override=False)


def _as_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_optional_bool(value: Optional[str]) -> Optional[bool]:
    if value is None or value.strip() == "":
        return None
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_csv(value: Optional[str]) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _as_int(value: Optional[str], default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _build_database_url() -> str:
    direct_url = os.getenv("DATABASE_URL")
    if direct_url:
        return direct_url

    pg_user = os.getenv("PGUSER")
    pg_password = os.getenv("PGPASSWORD")
    pg_host = os.getenv("PGHOST")
    pg_port = os.getenv("PGPORT", "5432")
    pg_database = os.getenv("PGDATABASE")

    if pg_user and pg_password and pg_host and pg_database:
        return (
            f"postgresql+pg8000://{quote_plus(pg_user)}:{quote_plus(pg_password)}"
            f"@{pg_host}:{pg_port}/{quote_plus(pg_database)}"
        )

    return "sqlite:///gwa_calculator.db"


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    secret_key: str
    database_url: str
    supabase_ssl_no_verify: bool
    access_token_expire_minutes: int
    cookie_name: str
    cookie_secure: Optional[bool]
    cookie_samesite: str
    cookie_domain: Optional[str]
    cors_allowed_origins: list[str]
    cors_allow_credentials: bool
    allowed_hosts: list[str]
    init_db_on_startup: bool
    seed_demo_data: bool
    reset_demo_passwords: bool
    default_admin_school_id: str
    default_admin_name: str
    default_admin_password: str
    db_pool_size: int
    db_max_overflow: int
    web_concurrency: int
    allow_sqlite_in_production: bool

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def database_backend(self) -> str:
        if self.database_url.startswith("postgresql"):
            return "postgresql"
        if self.database_url.startswith("sqlite"):
            return "sqlite"
        return "unknown"

    def validate(self) -> None:
        insecure_secret_values = {
            "",
            "your-secret-key-here",
            "dev-secret-change-me",
            "change-me-in-production",
            "changeme",
        }
        if self.is_production and (self.secret_key in insecure_secret_values or len(self.secret_key) < 32):
            raise RuntimeError(
                "SECRET_KEY must be set to a strong value (32+ chars) when APP_ENV=production."
            )

        if self.cookie_samesite not in {"lax", "strict", "none"}:
            raise RuntimeError("COOKIE_SAMESITE must be one of: lax, strict, none.")

        if self.is_production and self.database_backend == "sqlite" and not self.allow_sqlite_in_production:
            raise RuntimeError(
                "Production must use Postgres/Supabase. Set DATABASE_URL or PG* env vars, "
                "or explicitly set ALLOW_SQLITE_IN_PRODUCTION=1 to bypass."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    default_origins = (
        []
        if app_env == "production"
        else ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"]
    )
    cors_allowed_origins = _as_csv(os.getenv("CORS_ALLOWED_ORIGINS")) or default_origins

    settings = Settings(
        app_env=app_env,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        secret_key=os.getenv("SECRET_KEY", ""),
        database_url=_build_database_url(),
        supabase_ssl_no_verify=_as_bool(os.getenv("SUPABASE_SSL_NO_VERIFY"), False),
        access_token_expire_minutes=_as_int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"), 60),
        cookie_name=os.getenv("COOKIE_NAME", "access_token"),
        cookie_secure=_as_optional_bool(os.getenv("COOKIE_SECURE")),
        cookie_samesite=os.getenv("COOKIE_SAMESITE", "lax").strip().lower(),
        cookie_domain=(os.getenv("COOKIE_DOMAIN") or "").strip() or None,
        cors_allowed_origins=cors_allowed_origins,
        cors_allow_credentials=_as_bool(os.getenv("CORS_ALLOW_CREDENTIALS"), True),
        allowed_hosts=_as_csv(os.getenv("ALLOWED_HOSTS")) or ["*"],
        init_db_on_startup=_as_bool(os.getenv("INIT_DB_ON_STARTUP"), True),
        seed_demo_data=_as_bool(os.getenv("SEED_DEMO_DATA"), app_env != "production"),
        reset_demo_passwords=_as_bool(os.getenv("DEMO_RESET_PASSWORDS"), False),
        default_admin_school_id=os.getenv("DEFAULT_ADMIN_SCHOOL_ID", "admin").strip() or "admin",
        default_admin_name=os.getenv("DEFAULT_ADMIN_NAME", "Administrator").strip() or "Administrator",
        default_admin_password=os.getenv(
            "DEFAULT_ADMIN_PASSWORD",
            "" if app_env == "production" else "Strongadminpass123!",
        ),
        db_pool_size=_as_int(os.getenv("DB_POOL_SIZE"), 10),
        db_max_overflow=_as_int(os.getenv("DB_MAX_OVERFLOW"), 20),
        web_concurrency=max(1, _as_int(os.getenv("WEB_CONCURRENCY"), 2)),
        allow_sqlite_in_production=_as_bool(os.getenv("ALLOW_SQLITE_IN_PRODUCTION"), False),
    )
    settings.validate()
    return settings
