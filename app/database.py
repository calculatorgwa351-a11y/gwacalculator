import logging
import ssl
from pathlib import Path

import certifi
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings


settings = get_settings()
logger = logging.getLogger(__name__)

engine_kwargs: dict = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

database_url = settings.database_url

if database_url.startswith("sqlite"):
    try:
        parsed = make_url(database_url)
        db_file = parsed.database
        if db_file and db_file != ":memory:":
            db_path = Path(db_file)
            if not db_path.is_absolute():
                db_path = Path.cwd() / db_path
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with db_path.open("a", encoding="utf-8"):
                pass
    except Exception as exc:
        fallback_path = Path.cwd() / "gwa_calculator.db"
        logger.warning(
            "SQLite path is not writable for DATABASE_URL=%s (%s). Falling back to %s",
            database_url,
            exc,
            fallback_path,
        )
        database_url = f"sqlite:///{fallback_path.as_posix()}"
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = settings.db_pool_size
    engine_kwargs["max_overflow"] = settings.db_max_overflow

    if database_url.startswith("postgresql"):
        if settings.supabase_ssl_no_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        engine_kwargs["connect_args"] = {"ssl_context": ssl_context}

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
