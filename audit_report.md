# Audit Report - GWA Calculator

## UI & Functional Bugs

### 1. Missing Year and Semester in Grades
- **Issue**: The academic records (SubjectGrade) were missing `year` and `semester` fields in the database.
- **Reproduction Steps**:
  1. Add a grade with a specific year and semester.
  2. Refresh the dashboard.
  3. The grade will show as "YR -" and Semesters will be lost.
- **Fix**: Added `year` and `semester` columns to `SubjectGrade` model, updated Pydantic schemas, and fixed the API and frontend to handle these fields.

### 2. Broken CSV Export
- **Issue**: The CSV export logic used outdated CSS selectors that didn't match the new UI.
- **Reproduction Steps**:
  1. Add grades.
  2. Click "Export CSV".
  3. The resulting file is empty or contains "undefined".
- **Fix**: Updated the selectors in `main.js` to match the current template structure.

### 3. Missing Social API Endpoints
- **Issue**: The frontend attempted to call `/api/posts/{id}/react` and `/api/posts/{id}/comments`, but these were not implemented in the backend.
- **Reproduction Steps**:
  1. Try to like a post or add a comment.
  2. Check the console for 404 errors.
- **Fix**: Implemented full reaction and comment functionality in the backend.

### 4. Missing Chart Timeline API
- **Issue**: The dashboard chart attempted to fetch data from `/api/analytics/user-timeline`, which didn't exist.
- **Reproduction Steps**:
  1. Open the dashboard.
  2. The chart remains empty or shows an error.
- **Fix**: Implemented the `/api/analytics/user-timeline` API.

## Technical Debt & Refactoring

- **Monolithic app.py**: The entire backend was in a single file. Refactored into a modular package structure:
  - `app/database.py`: DB configuration.
  - `app/models.py`: SQLAlchemy models.
  - `app/schemas.py`: Pydantic schemas.
  - `app/auth.py`: Security and JWT logic.
  - `app/crud.py`: DB utility functions.
  - `app/routers/`: Modular route handlers for pages, API, and admin.
- **Performance**: Optimized the social feed API to use `joinedload` (eager loading), eliminating N+1 query problems.

## Visualization Enhancements

- **Interactive Tooltips**: Added detailed tooltips to the GWA chart with custom styling.
- **Data Points**: Improved visibility of data points with customized radius and hover effects.
- **Better Scales**: Improved chart scales for GWA visualization (reverse Y-axis for Philippine grading system).
