# GWA Calculator (Refactored to Vue 3 + TypeScript)

A modern FastAPI and Vue 3 application for students to manage academic grades and share updates. Built with the Philippine GWA system in mind.

## 🚀 Refactoring Overview
This project has been refactored from a traditional server-side rendered (Jinja2) Flask-style app to a modern Single Page Application (SPA) using:
- **Frontend**: Vue 3 (Composition API), TypeScript, Vite
- **State Management**: Pinia
- **Styling**: Tailwind CSS
- **Testing**: Vitest (Unit), Cypress (E2E)
- **Linting & Formatting**: ESLint, Prettier

### 🛡️ Architecture Decisions
1.  **TypeScript First**: All components and stores use TypeScript interfaces for type safety and to catch bugs at compile time.
2.  **Centralized State**: Theme management and user authentication are handled by Pinia stores to eliminate variable redeclaration issues (e.g., the `themeToggle` error).
3.  **Robust Error Handling**:
    -   **Global Error Handler**: Catches all runtime errors and unhandled promise rejections.
    -   **`errorCaptured` Hook**: Used in `App.vue` to intercept errors in the component tree.
4.  **Vite Build Tool**: Used for lightning-fast development and optimized production builds.

## 🔑 Login Credentials
- **Admin**: `admin` / `adminpass`
- **Students**: `2024xxxx` / `password123` (any 2024xxxx school ID)

## 🐳 Docker-Based Monitoring
The project is configured to run in Docker with automated error resolution.
```bash
docker-compose up --build
```

## 💻 Local Development Setup
1.  **Install Dependencies**:
    ```bash
    npm install
    ```
2.  **Start the Backend (FastAPI)**:
    ```bash
    python -m app.main
    ```
3.  **Start the Frontend (Vite)**:
    ```bash
    npm run dev
    ```

## 🧪 Testing
- **Unit Tests**: `npm run test:unit` (Targeting >80% coverage)
- **End-to-End Tests**: `npm run test:e2e` (Using Cypress)

## 🛠️ Troubleshooting
### "themeToggle has already been declared"
This issue was resolved by moving the theme-switching logic into a centralized Pinia store (`src/stores/theme.ts`). In the new architecture, components interact with the store's reactive `isDark` state and `toggleTheme` method, preventing any identifier collisions.

### API Connection Errors
Ensure the FastAPI backend is running on `http://localhost:5001`. The Vite dev server is configured to proxy all `/api` requests to the backend.

---
