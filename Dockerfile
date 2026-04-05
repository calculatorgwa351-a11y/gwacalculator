FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

ENV NPM_CONFIG_FETCH_RETRIES=8 \
    NPM_CONFIG_FETCH_RETRY_FACTOR=2 \
    NPM_CONFIG_FETCH_RETRY_MINTIMEOUT=20000 \
    NPM_CONFIG_FETCH_RETRY_MAXTIMEOUT=120000 \
    NPM_CONFIG_FETCH_TIMEOUT=300000

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
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PIP_RETRIES=12

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos "" appuser
RUN mkdir -p /data && chown -R appuser:appuser /data

COPY requirements.txt ./
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY app ./app
COPY init.py ./init.py
COPY gunicorn.conf.py ./gunicorn.conf.py
COPY --from=frontend-builder /app/frontend/dist ./dist

RUN chown -R appuser:appuser /app /data
USER appuser

EXPOSE 5000

CMD ["sh", "-c", "gunicorn app.main:app -c gunicorn.conf.py"]
