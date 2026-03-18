# Changelog - GWA Calculator

## [2.1.0] - 2026-03-19

### Added
- Modular backend structure (app/ submodules).
- `year` and `semester` fields to `SubjectGrade` model and schemas.
- `/api/analytics/user-timeline` endpoint for GWA chart.
- `/api/posts/{post_id}/react` and `/api/posts/{post_id}/comments` endpoints for social features.
- Unit and integration tests in `tests/`.
- Interactive tooltips and improved data points for GWA chart.
- Eager loading (joinedload) for posts and comments to optimize performance.

### Fixed
- CSV Export: Updated selectors to match the current UI structure.
- Grade Record: Year and semester are now properly saved to the database.
- Social Feed: Reactions and comments now correctly update and persist.
- Chart Loading: Dashboard chart now fetches real-time data from the new timeline API.

### Changed
- Refactored monolithic `app.py` into a modular package.
- Updated FastAPI version in `requirements.txt`.
- Improved GWA chart styling with better scales and interaction modes.
