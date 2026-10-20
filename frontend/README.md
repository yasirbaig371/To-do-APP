# Phase 3: React frontend

Daymark is a responsive React + TypeScript interface connected to the FastAPI
API. It includes public sign-in/registration, personal dashboards and task
management, profile/password forms, and admin statistics and user management.
All task and account data comes from the API; the frontend does not use sample
task data.

## Run on Windows

Prerequisites: Node.js 20.19+ (or 22.12+) and the Phase 2 backend configured
and running at `http://localhost:8000`.

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open the printed Vite address (normally `http://localhost:5173`). Use this
`localhost` address so it matches the example backend CORS origin. The example
API base URL points to the local backend. If the API is on another origin,
change `VITE_API_BASE_URL` in `frontend\.env` to its `/api` URL and add the
frontend origin to `CORS_ORIGINS` in `backend\.env`, then restart the API.

## Frontend features

- Register and sign in; users and admins are sent to their respective dashboards.
- User dashboard statistics and recently added tasks.
- Search, status/priority filtering, sorting, and pagination for tasks.
- Task create, detail, edit, complete/reopen, and delete with confirmation.
- Profile updates and password change.
- Admin system statistics, account search/filters, activation, and role management.
- Loading, empty, validation, API error, and expired-session states.
- Responsive, keyboard-friendly navigation and accessible form labels.

## Token handling

The short-lived access token is kept in JavaScript memory only. It is not put in
`localStorage`, `sessionStorage`, a URL, or a cookie. This reduces persistence
and exposure to tokens left on a shared browser, but a page reload clears the
session and requires the user to sign in again. A 401 response clears the
in-memory session and returns protected pages to sign-in. Logout discards the
token; the backend is stateless, so an already-issued token remains valid until
it expires. HTTPS is required in production.

## Checks

```powershell
npm run build
```

This runs the TypeScript project build and creates the production bundle in
`dist\`. Start the backend separately with `uvicorn app.main:app --reload`.
Then register a development user in the UI, create a task, refresh the task
list, and confirm the task persists from the API/database. Admin UI requires an
account created by the controlled backend bootstrap command.
