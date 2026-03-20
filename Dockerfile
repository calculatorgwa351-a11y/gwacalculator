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

COPY requirements.txt ./
RUN pip install --no-cache-dir --default-timeout=180 --retries 8 -r requirements.txt

COPY app ./app
COPY init.py ./init.py
COPY --from=frontend-builder /app/frontend/dist ./dist

EXPOSE 5000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5000} --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips=*"]
