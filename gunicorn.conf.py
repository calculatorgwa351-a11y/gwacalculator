import os


bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
database_url = os.getenv("DATABASE_URL", "")
<<<<<<< HEAD
default_workers = "1" if database_url.startswith("sqlite") else "2"
=======

# Default to a single worker unless we know we're on a non-SQLite database.
# Local Docker runs often omit DATABASE_URL, which falls back to SQLite in app config.
default_workers = "2" if database_url.startswith("postgresql") else "1"
>>>>>>> abbdb4d (Initial commit)
workers = int(os.getenv("WEB_CONCURRENCY", default_workers))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
