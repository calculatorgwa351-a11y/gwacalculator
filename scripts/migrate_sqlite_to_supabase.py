from __future__ import annotations

import argparse
import ssl
from pathlib import Path
import sys
from typing import Iterable

import certifi
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.inspection import inspect as sa_inspect

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.database import Base
from app.config import get_settings
from app.models import Admin, AdminAudit, Comment, Course, Department, Post, Reaction, SubjectGrade, User


load_dotenv(override=False)

TABLE_MODELS = [
    Department,
    Course,
    User,
    Admin,
    SubjectGrade,
    Post,
    Comment,
    Reaction,
    AdminAudit,
]


class MigrationError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="One-time migration from local SQLite to Supabase/Postgres."
    )
    parser.add_argument(
        "--source",
        default=str(REPO_ROOT / "gwa_calculator.db"),
        help="Path to the local SQLite database file. Defaults to <repo>/gwa_calculator.db",
    )
    parser.add_argument(
        "--target-url",
        default="",
        help="Target Postgres/Supabase DATABASE_URL. Defaults to the current environment configuration.",
    )
    return parser.parse_args()


def model_columns(model) -> list[str]:
    return [column.key for column in sa_inspect(model).columns]


def row_to_dict(row, column_names: Iterable[str]) -> dict:
    return {column_name: getattr(row, column_name) for column_name in column_names}


def count_rows(session: Session, model) -> int:
    return session.query(model).count()


def quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def reset_postgres_sequence(engine, model, inserted_count: int) -> None:
    if inserted_count <= 0:
        return

    table_name = model.__table__.name
    quoted_table = quote_identifier(table_name)
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{quoted_table}', 'id'),
                    (SELECT MAX(id) FROM {quoted_table}),
                    true
                )
                """
            )
        )


def normalize_error(exc: Exception) -> MigrationError:
    message = str(exc)
    lowered = message.lower()

    if "password authentication failed" in lowered:
        return MigrationError(
            "Supabase rejected the database password. Update PGPASSWORD or DATABASE_URL in .env "
            "with the current Supabase Postgres credentials, then rerun the migration."
        )

    if "target database is not empty" in lowered:
        return MigrationError(message)

    if "could not translate host name" in lowered or "name or service not known" in lowered:
        return MigrationError(
            "The Postgres host could not be resolved. Check PGHOST or DATABASE_URL in .env."
        )

    if isinstance(exc, SQLAlchemyError):
        return MigrationError(f"Database migration failed: {message}")

    return MigrationError(message)


def main() -> int:
    args = parse_args()
    settings = get_settings()

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists():
        raise MigrationError(f"Source SQLite database not found: {source_path}")

    source_url = f"sqlite:///{source_path.as_posix()}"
    target_url = (args.target_url or settings.database_url).strip()

    if not target_url:
        raise MigrationError("Target DATABASE_URL is empty. Set Supabase credentials first.")
    if target_url.startswith("sqlite"):
        raise MigrationError("Target database must be Supabase/Postgres, not SQLite.")

    source_engine = create_engine(source_url, connect_args={"check_same_thread": False})
    target_engine_kwargs = {}
    if target_url.startswith("postgresql"):
        if settings.supabase_ssl_no_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        else:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        target_engine_kwargs["connect_args"] = {"ssl_context": ssl_context}

    target_engine = create_engine(target_url, **target_engine_kwargs)

    source_inspector = inspect(source_engine)
    source_tables = set(source_inspector.get_table_names())

    Base.metadata.create_all(bind=target_engine)

    SourceSession = sessionmaker(bind=source_engine, autoflush=False, autocommit=False)
    TargetSession = sessionmaker(bind=target_engine, autoflush=False, autocommit=False)

    source_session = SourceSession()
    target_session = TargetSession()

    try:
        nonempty_tables = {}
        for model in TABLE_MODELS:
            if count_rows(target_session, model) > 0:
                nonempty_tables[model.__table__.name] = count_rows(target_session, model)

        if nonempty_tables:
            joined = ", ".join(f"{table}={count}" for table, count in nonempty_tables.items())
            raise MigrationError(
                "Target database is not empty. Use a fresh Supabase database before rerunning. "
                f"Non-empty tables: {joined}"
            )

        source_counts: dict[str, int] = {}
        copied_counts: dict[str, int] = {}
        skipped_tables: list[str] = []

        try:
            for model in TABLE_MODELS:
                table_name = model.__table__.name
                if table_name not in source_tables:
                    skipped_tables.append(table_name)
                    source_counts[table_name] = 0
                    copied_counts[table_name] = 0
                    continue

                query = source_session.query(model)
                if hasattr(model, "id"):
                    query = query.order_by(getattr(model, "id").asc())
                rows = query.all()
                source_counts[table_name] = len(rows)

                if not rows:
                    copied_counts[table_name] = 0
                    continue

                payloads = [row_to_dict(row, model_columns(model)) for row in rows]
                target_session.execute(model.__table__.insert(), payloads)
                copied_counts[table_name] = len(payloads)

            target_session.commit()
        except Exception:
            target_session.rollback()
            raise

        for model in TABLE_MODELS:
            reset_postgres_sequence(target_engine, model, copied_counts.get(model.__table__.name, 0))

        verification_counts = {
            model.__table__.name: count_rows(target_session, model)
            for model in TABLE_MODELS
        }

        mismatches = []
        for model in TABLE_MODELS:
            table_name = model.__table__.name
            expected = source_counts.get(table_name, 0)
            actual = verification_counts.get(table_name, 0)
            if expected != actual:
                mismatches.append(f"{table_name}: source={expected}, target={actual}")

        target_parsed = make_url(target_url)
        print("Migration complete.")
        print(f"Source SQLite: {source_path}")
        print(
            "Target Postgres: "
            f"{target_parsed.host or 'unknown-host'}/{target_parsed.database or 'unknown-db'}"
        )

        for model in TABLE_MODELS:
            table_name = model.__table__.name
            print(
                f"{table_name}: source={source_counts.get(table_name, 0)} "
                f"copied={copied_counts.get(table_name, 0)} "
                f"target={verification_counts.get(table_name, 0)}"
            )

        if skipped_tables:
            print("Skipped missing source tables: " + ", ".join(skipped_tables))

        if mismatches:
            raise MigrationError("Verification failed: " + "; ".join(mismatches))

        print("Verification passed.")
        return 0
    finally:
        source_session.close()
        target_session.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MigrationError as exc:
        raise SystemExit(f"Migration failed: {exc}") from None
    except Exception as exc:
        raise SystemExit(f"Migration failed: {normalize_error(exc)}") from None
