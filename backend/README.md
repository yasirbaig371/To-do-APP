# Phase 2: FastAPI backend

The API uses FastAPI, SQLAlchemy 2, PostgreSQL, Alembic, Pydantic v2,
Argon2 password hashes, and short-lived JWT access tokens. It supports user
registration/profile management, task CRUD and filtering, per-user statistics,
and protected admin user management. Admins do not gain access to another
user's task records.

## Important files

- `app/main.py`: API app, CORS configuration, routes, and health endpoint.
- `app/core/config.py`: required environment-based settings.
- `app/core/security.py`: Argon2 hash operations and JWT creation/validation.
- `app/db/session.py`, `app/db/base.py`: SQLAlchemy engine/session and ORM base.
- `app/models/`: database-backed user/task models and enums.
- `app/schemas/`: request validation and response models; sensitive fields are
  never returned.
- `app/api/routes/`: authentication, profile, task, and admin endpoints.
- `app/api/deps.py`: authenticated-user and admin authorization dependencies.
- `app/cli.py`: controlled administrator bootstrap with hidden password prompts.
- `alembic/versions/0001_initial_schema.py`: initial migration for a new database.
- `tests/`: isolated SQLite API and authorization tests.

## Configure and run on Windows

Prerequisites: Python 3.11 or later, PostgreSQL, and the
Phase 1 database/user. In PowerShell:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` locally. Use the database and role you created (for this
setup: `todo_db` and `todo_user`) and replace the password placeholder with
your URL-encoded local database password. Do not commit `.env`. Do not paste
database passwords or JWT secrets into chat. Generate a JWT secret locally:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy that output into `JWT_SECRET_KEY` in `.env`. The example CORS origin is
Vite's `http://localhost:5173`; change it when the frontend origin is known.

For the AI assistant, create an API key in your OpenRouter account and set
`OPENROUTER_API_KEY` in `.env`. The default model is
`liquid/lfm-2.5-2.6b:free`; set `OPENROUTER_MODEL` to another OpenRouter model
that supports tool calling if desired. Keep the key in the backend `.env` only.
Alternatively, configure `OPENAI_API_KEY` and `OPENAI_MODEL` to use OpenAI
directly. OpenRouter settings take precedence when both providers are set. If
chat reports that no API key is configured, ensure one of these variables has
a non-empty value in `backend\.env`, start Uvicorn from the `backend\` folder,
and restart the backend after changing the file.

### Database migration

For a new, empty database, from `backend` after configuring `.env`:

```powershell
alembic upgrade head
```

If Phase 1's `database\schema.sql` has already created this exact schema,
**do not run that initial migration on top of it**. Record the current schema
as the initial Alembic baseline instead:

```powershell
alembic stamp head
```

Afterward, use Alembic for future schema changes. The migration is checked into
source control; no credentials are stored in it.

### Start the API and Swagger UI

```powershell
uvicorn app.main:app --reload
```

Expected: Uvicorn serves `http://127.0.0.1:8000`; `/health` returns
`{"status":"ok"}`, Swagger UI is at `/docs`, and OpenAPI JSON is at `/openapi.json`.
The app intentionally does not create tables at startup; run Alembic first.

## Create the first administrator

Bootstrap the initial administrator through a local command, not public
registration. From `backend`:

```powershell
python -m app.cli create-admin --email admin@example.com --full-name "Todo Admin"
```

The password is entered twice through hidden prompts and stored as Argon2.
Choose a unique email. Public registration ignores extra role fields and always
creates a regular user. Admin role changes are protected and cannot remove or
deactivate the last active administrator.

## API outline

All routes use the `/api` prefix:

| Area | Routes |
|---|---|
| Authentication | `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout` |
| Profile | `GET /users/me`, `PATCH /users/me`, `POST /users/me/change-password`, `GET /users/me/statistics` |
| Tasks | `POST /tasks`, `GET /tasks`, `GET /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}` |
| Administration | `GET /admin/users`, `GET /admin/users/{id}`, `PATCH /admin/users/{id}/status`, `PATCH /admin/users/{id}/role`, `GET /admin/statistics` |

Login uses OAuth2 form encoding: the `username` field contains the email and
`password` contains the password. Swagger's Authorize flow uses this same
format. Authenticated requests use `Authorization: Bearer <access_token>`.

Task list supports `status`, `priority`, `search`, `sort_by`, `sort_order`,
`limit` (1–100), and `offset` (0–100000). Admin user listing supports `search`,
`role`, `is_active`, `limit`, and `offset`. A task belonging to another user
returns 404, including when requested by an administrator.

Example request sequence in Swagger:

1. `POST /api/auth/register` with
   `{"full_name":"Example User","email":"user@example.com","password":"at-least-12-characters"}`.
   Expected: 201 and a user profile without password data.
2. `POST /api/auth/login` using form fields `username=user@example.com` and
   `password=at-least-12-characters`. Expected: 200 with a bearer access token.
3. Select **Authorize**, enter the username/email and password, then call
   `POST /api/tasks` with `{"title":"Read API docs","priority":"medium"}`.
   Expected: 201 with a pending task and its owner ID.
4. Call `GET /api/tasks?status=pending`; expected: the task just created.
5. Patch that task with `{"status":"completed"}`; expected: completed status
   and a UTC completion timestamp.

## Authentication and production notes

- Passwords are hashed with Argon2; password hashes are never serialized.
- Access tokens are signed JWTs with a 15-minute default lifetime. Logout is
  stateless: the client discards its token. A stolen token remains usable until
  expiry, so use HTTPS, short lifetimes, and secure client storage. A future
  revocation requirement needs server-side sessions/token versioning.
- Inactive accounts are rejected at login and on every authenticated request.
- Login has a 5-attempts-per-minute in-memory rate limit per client IP. This
  works for a single development process; production multi-worker deployments
  should configure shared Redis-backed rate-limit storage and a trusted proxy.
- Restrict CORS to the real frontend origin. Deploy only behind HTTPS, keep
  secrets in a deployment secret manager, rotate JWT secrets deliberately, and
  use a non-superuser database role with least privilege.
- Admin access is limited to user management and system statistics; it does not
  permit reading or changing users' task details.

## Tests

Tests use a temporary in-memory SQLite database and never connect to or modify
the configured PostgreSQL database:

```powershell
python -m pytest -q
```

Expected: all tests pass. Coverage includes registration/duplicate email,
password hashing, login and invalid tokens, inactive users, profile and
password changes, task CRUD/isolation, filtering/pagination/validation,
statistics, admin-only access, login rate limiting, and last-admin protection.

## Phase 2 checklist

- [x] Implement the FastAPI API, SQLAlchemy models, security, and admin/user permissions.
- [x] Add the initial Alembic migration and baseline-stamping instructions for the Phase 1 SQL schema.
- [x] Pass the automated SQLite suite (12 tests).
- [x] Pass a disposable PostgreSQL migration/API integration check and an HTTP/Swagger smoke test.
- [x] Configure and verify this machine's `todo_db` / `todo_user` database; Alembic baseline stamped and current version confirmed at `0001_initial`.
- [x] User explicitly approved moving to Phase 3.
