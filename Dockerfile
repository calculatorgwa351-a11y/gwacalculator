FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY package*.json ./
RUN npm ci

COPY index.html ./
COPY vite.config.ts ./
COPY tsconfig*.json ./
COPY postcss.config.cjs ./
COPY tailwind.config.cjs ./
COPY src ./src

RUN npm run build


FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" appuser
RUN mkdir -p /data && chown -R appuser:appuser /data

COPY requirements.txt ./
RUN pip install --no-cache-dir --default-timeout=180 --retries 8 -r requirements.txt

COPY app ./app
COPY init.py ./init.py
COPY gunicorn.conf.py ./gunicorn.conf.py
COPY --from=frontend-builder /app/frontend/dist ./dist

RUN chown -R appuser:appuser /app /data
USER appuser

EXPOSE 5000

CMD ["sh", "-c", "gunicorn app.main:app -c gunicorn.conf.py"]
