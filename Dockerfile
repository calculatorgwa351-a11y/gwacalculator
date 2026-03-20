# --- Stage 1: Build Frontend ---
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install dependencies separately for better caching
COPY package*.json ./
RUN npm ci

# Copy all files for building the frontend
COPY . .
RUN npm run build

# --- Stage 2: Build Backend & Runtime ---
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend assets from Stage 1 to backend's dist folder
COPY --from=frontend-builder /app/frontend/dist ./dist

# Expose port and run the FastAPI app
EXPOSE 5000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
