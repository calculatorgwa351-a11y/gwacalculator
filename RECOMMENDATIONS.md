# GWAcalculator: Recommendations (Codebase Review)

## Top Priorities

- Replace hardcoded secret key and config
  - Move secrets and config to environment variables. Replace the hardcoded SECRET_KEY and DB URI in [app.py](file:///d:/gwacalculator/app.py#L10-L13) with env-driven config (e.g., python-dotenv + config.py).
  - Set secure session defaults in production (SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SECURE=True, SESSION_COOKIE_SAMESITE='Lax').

- Remove unsafe debug/admin backdoors
  - Delete or hard-gate the debug endpoint that resets admin credentials in [app.py](file:///d:/gwacalculator/app.py#L479-L492). This leaks admin creds.
  - Do not run with debug=True in production. See [app.py](file:///d:/gwacalculator/app.py#L494-L495).

- Add CSRF protection
  - Enable CSRF for forms and JSON endpoints. Integrate Flask-WTF CSRFProtect and include tokens in requests (add header for fetch).

- Harden authentication and admin access
  - Add simple rate limiting on login and /admin-auth (Flask-Limiter).
  - Consider making analytics endpoints require authentication or admin where appropriate (currently public: [app.py](file:///d:/gwacalculator/app.py#L312-L374)).

## Architecture & Structure

- Adopt the application factory pattern
  - Split monolithic [app.py](file:///d:/gwacalculator/app.py) into package:
    - app/__init__.py (create_app, register extensions)
    - app/models.py
    - app/blueprints/{auth,posts,grades,admin,analytics}
    - app/config.py (Dev/Prod/Test configs)

- Add database migrations
  - Introduce Flask-Migrate/Alembic for schema changes instead of manual create_all in [init_db.py](file:///d:/gwacalculator/init_db.py#L1-L39).

- Configuration via .env
  - Add python-dotenv and .env.example. Load SECRET_KEY, SQLALCHEMY_DATABASE_URI, and DEBUG.

## Data Model & Performance

- Indices and constraints
  - Add indexes for frequently filtered columns (Post.user_id, Reaction.post_id/user_id, SubjectGrade.user_id). Consider unique constraint for Reaction (post_id, user_id).

- N+1 queries and payload shaping
  - The posts API builds reactions/comments per post which can trigger lazy loads. Consider eager loading or aggregation queries in [app.py](file:///d:/gwacalculator/app.py#L171-L203).
  - In comments GET, avoid per-row user lookup [app.py](file:///d:/gwacalculator/app.py#L238-L251). Join or prefetch author names.

- Validation & lengths
  - Enforce max lengths consistently (e.g., Post.content, Comment.content). Add server-side length checks and better error messages.

## API Surface

- Consistent error handling
  - Create a small error handler that returns JSON for API routes with consistent schema {error, details}.

- Input validation
  - Validate and clamp numeric ranges for grades/units in all relevant endpoints, ensure subject non-empty (already partly done in [app.py](file:///d:/gwacalculator/app.py#L253-L281), extend to update endpoint).

- Authorization
  - Reassess which analytics endpoints need login or admin ([app.py](file:///d:/gwacalculator/app.py#L312-L374)).

## Frontend

- Remove duplicate script include
  - [base.html](file:///d:/gwacalculator/templates/base.html#L21-L22) and [base.html](file:///d:/gwacalculator/templates/base.html#L86-L89) both include main.js. Keep only one.

- CSRF integration
  - Add CSRF token to fetch requests in [main.js](file:///d:/gwacalculator/static/js/main.js) and [admin.js](file:///d:/gwacalculator/static/js/admin.js) once server-side is enabled.

- Feature completeness
  - Implement edit grade UI (buttons exist in [dashboard.html](file:///d:/gwacalculator/templates/dashboard.html#L91-L94) and events scaffolded in [main.js](file:///d:/gwacalculator/static/js/main.js#L167-L215), but no edit modal/flow).
  - Add delete grade action.
  - Add pagination or lazy load for posts in [main.js](file:///d:/gwacalculator/static/js/main.js#L74-L81) and server-side limit parameters.

## Developer Experience

- Update README instructions
  - Align venv name with the repo (.venv vs venv). Current README uses “venv” steps; project contains “.venv” ([README.md](file:///d:/gwacalculator/README.md#L12-L18)).
  - Add Windows PowerShell activation note (use .\\.venv\\Scripts\\Activate.ps1).

- Add tooling
  - Add formatting/linting: black, isort, flake8/ruff.
  - Add pre-commit config.

- Testing
  - Introduce pytest with a minimal test matrix:
    - Unit tests for compute_gwa_for_user ([app.py](file:///d:/gwacalculator/app.py#L115-L123)).
    - Auth and posts API tests.
    - Admin endpoints authorization tests.

## Deployment

- WSGI server and config
  - Add gunicorn (Linux) or waitress (Windows) entrypoint. Provide app factory “create_app” for production servers.
  - Set Flask env via environment (FLASK_ENV, FLASK_APP) and disable debug in production.

- Static assets
  - Consider pinning Tailwind via a build step, or keep CDN with Subresource Integrity.

## Suggested Package Additions

- python-dotenv, Flask-Migrate, Flask-WTF (CSRFProtect), Flask-Limiter
- gunicorn or waitress (depending on target)

## Quick Wins Summary

1) Remove /api/debug/reset-admin and set debug=False in production.  
2) Move SECRET_KEY/DB URI to env config and set secure session flags.  
3) Remove duplicate main.js include in base layout.  
4) Add CSRF protection and rate limiting to auth endpoints.  
5) Add migrations; then consider model indexes and unique reaction constraint.  
6) Add tests for compute GWA and basic API flows.

