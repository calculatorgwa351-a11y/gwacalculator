# GWA Calculator

FastAPI + Vue 3 application for grade tracking, GWA computation, student feed, and admin analytics.

## Tech Stack
- Backend: FastAPI, SQLAlchemy
- Frontend: Vue 3, Vite, Pinia, Chart.js
- Runtime: Docker Compose

## Local Development
1. Install frontend packages:
   - `npm install`
2. Run backend:
   - `python -m app.main`
3. Run frontend:
   - `npm run dev`

## Production (Docker)
1. Copy environment file and set secure values:
   - `copy .env.example .env`
2. Edit `.env` and set at least:
   - `APP_ENV=production`
   - `SECRET_KEY=<strong-random-32+-char-value>`
   - `DEFAULT_ADMIN_PASSWORD=<secure-bootstrap-password>`
   - `CORS_ALLOWED_ORIGINS=<comma-separated-prod-origins>`
   - `ALLOWED_HOSTS=<your-domain,localhost>`
3. Build and run:
   - `docker compose up --build -d`
4. Verify health:
   - `http://localhost:5000/api/health`

## Render Deploy
- This repo now deploys on Render as a **Docker web service** (`render.yaml`).
- Docker is required so the frontend `dist` bundle is built and served by FastAPI at `/`.
- If you see `{"detail":"Not Found"}` on `/`, your Render service is still using native Python runtime.

## Default Demo Credentials
- Admin: `admin / adminpass` (development/demo only)
- Seeded students: `2024xxxx / password123`

## Validation Commands
- `npm run type-check`
- `npm run test:unit`
- `npm run build-only`
- `docker compose build`

## Notes
- In production mode, startup fails if `SECRET_KEY` is weak or missing.
- Demo seeding is controlled with `SEED_DEMO_DATA` (defaults to `0` in production compose).
