# Full-Stack To-Do List

This project is being delivered in three explicitly gated phases. Phase 1
contains the PostgreSQL schema and setup guide under `database\`. Phase 2
contains the FastAPI backend under `backend\`. React frontend work is not
included and will not begin until the backend phase is approved.

## Phase status

- [x] Phase 1 database schema and local verification against a temporary PostgreSQL database.
- [x] Phase 2 backend implementation, tests, and verification against the configured database.
- [x] Phase 3 React frontend implementation and integration checks.

## Final verification

- [x] Backend tests pass.
- [x] Frontend TypeScript build passes.
- [x] Browser integration verified against the PostgreSQL-backed API.
- [x] Task persistence, role-based navigation, admin guard responses, and mobile layout checked.
- [ ] User review/acceptance.

For the Phase 1 database design and setup, see [database/README.md](database/README.md).
For backend configuration, migrations, API usage, security decisions, and tests,
see [backend/README.md](backend/README.md).
For frontend setup, API connection, and token-storage trade-offs, see
[frontend/README.md](frontend/README.md).
