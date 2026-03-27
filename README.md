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
   - `PGUSER=<supabase-user>`
   - `PGPASSWORD=<supabase-password>`
   - `PGHOST=<supabase-host>`
   - `PGPORT=6543`
   - `PGDATABASE=postgres`
   - `CORS_ALLOWED_ORIGINS=<comma-separated-prod-origins>`
   - `ALLOWED_HOSTS=<your-domain,localhost>`
3. Build and run:
   - `docker compose up --build -d`
4. Verify health:
   - `http://localhost:5000/api/health`
   - confirm `database_backend` is `postgresql`
5. Run the production readiness check:
   - `npm run check:production`

## Render Deploy
- This repo now deploys on Render as a **Docker web service** (`render.yaml`).
- Docker is required so the frontend `dist` bundle is built and served by FastAPI at `/`.
- If you see `{"detail":"Not Found"}` on `/`, your Render service is still using native Python runtime.
- Set `DATABASE_URL` in Render to your Supabase Postgres connection string.
- Set `SUPABASE_SSL_NO_VERIFY=1` only if your specific Supabase connection requires relaxed SSL verification.
- The Docker image now starts through `gunicorn` + `uvicorn` workers for a more production-ready FastAPI runtime.

## Default Demo Credentials
- Admin: `admin / Strongadminpass123!` (development/demo only)
- Seeded students: `2024xxxx / password123`

## Supabase Migration
1. Ensure local `.env` points to Supabase credentials.
2. Keep the current local SQLite file as the migration source:
   - `gwa_calculator.db`
3. Run the one-time migration from the project root:
   - `npm run migrate:supabase`
4. Or run the Windows wrapper from anywhere:
   - `C:\Users\keith\Documents\projects\gwacalculator\migrate-to-supabase.cmd`
   - PowerShell alternative:
   - `& "C:\Users\keith\Documents\projects\gwacalculator\migrate-to-supabase.ps1"`
5. Optional custom source file:
   - `npm run migrate:supabase -- --source C:\path\to\gwa_calculator.db`
6. If migration fails with a password error, update `PGPASSWORD` or `DATABASE_URL` in `.env` with the current Supabase database password, then rerun.
7. Verify the summary shows matching source and target row counts.
8. Start the app and confirm `/api/health` reports `database_backend: postgresql`.

## Validation Commands
- `npm run type-check`
- `npm run test:unit`
- `npm run build-only`
- `npm run check:production`
- `npm run prepare:production`
- `docker compose build`
- `npm run migrate:supabase -- --help`

## Notes
- In production mode, startup fails if `SECRET_KEY` is weak or missing.
- In production mode, startup also fails if the app still points to SQLite unless `ALLOW_SQLITE_IN_PRODUCTION=1` is explicitly set.
- Demo seeding is controlled with `SEED_DEMO_DATA` and should stay `0` when using a real Supabase database.
- The app now reports the active database backend and target via `/api/health`.
