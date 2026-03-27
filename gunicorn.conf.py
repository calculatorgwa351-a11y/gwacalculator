import os


bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
database_url = os.getenv("DATABASE_URL", "")
default_workers = "1" if database_url.startswith("sqlite") else "2"
workers = int(os.getenv("WEB_CONCURRENCY", default_workers))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info").lower()
