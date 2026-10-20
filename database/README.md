# Phase 1: PostgreSQL database

This folder contains the PostgreSQL schema and seed data from Phase 1. The
FastAPI/SQLAlchemy application and Alembic migration are in `../backend`; the
React frontend remains gated on backend approval. The schema is plain
PostgreSQL SQL so it can be created and verified independently.

## Data model

- `users` stores account and authorization metadata. `password_hash` stores a
  password hash, never a plaintext password. Public registration must use the
  database default role (`user`); admin creation will be handled through a
  controlled backend bootstrap operation in Phase 2.
- `tasks` stores each task and its owner. The non-null foreign key guarantees
  every task has an owner. Deleting a user cascades to their tasks.
- No additional tables are needed for the requested features.

```text
+-------------------------------+       1       0..*
| users                         |----------------------| tasks
| PK id                          |                      | PK id
|    full_name                   |                      |    title
| UQ lower(trim(email))          |                      |    description
|    password_hash               |                      |    status
|    role                         |                      |    priority
|    is_active                    |                      |    due_date
|    created_at                  |                      | FK owner_id -> users.id
|    updated_at                  |                      |    created_at
+-------------------------------+                       |    updated_at
                                                        |    completed_at
                                                        +-------------------+
```

The relationship is one-to-many: a user can own zero or more tasks, and every
task belongs to exactly one user. Primary keys are generated `BIGINT` identity
values. Email uniqueness is case- and surrounding-whitespace-insensitive.
Enums constrain roles, statuses, and priorities to the allowed values. A check
constraint ensures completed tasks have `completed_at`, and non-completed tasks
do not.

All timestamps use `TIMESTAMPTZ`, which stores an absolute instant; PostgreSQL
converts it for display according to the client session timezone. Use UTC for
application connections and output. `updated_at` is maintained by database
triggers on updates.

Indexes support user task lists and status/priority filters, and help find tasks
with due dates. Database transactions preserve atomicity when creating or
updating related data. The application must still scope task queries by the
authenticated owner's ID.

## Prerequisites and database creation

Install a supported PostgreSQL release (PostgreSQL 16 or newer recommended)
from [the official PostgreSQL downloads page](https://www.postgresql.org/download/).
The installation should include the `psql` command-line client. On Windows,
start the PostgreSQL service using the Services application or the service
manager installed with PostgreSQL.

In PowerShell, connect as a PostgreSQL administrator and create a dedicated
development database role and database. `psql` prompts for passwords; enter
them at the prompt rather than placing them in a command or source file:

```powershell
psql -h localhost -U postgres
```

At the `postgres=#` prompt, use your own strong local development password:

```sql
CREATE ROLE todo_user LOGIN;
\password todo_user
CREATE DATABASE todo_db OWNER todo_user;
\q
```

The role has no administrative privileges. Do not reuse this development
password in production. Keep credentials in a local environment/secret store;
never commit them or paste them into chat. For later application configuration,
the SQLAlchemy URL will use the form
`postgresql+psycopg://todo_user:<URL-encoded-password>@localhost:5432/todo_db`.
The backend phase will provide the actual environment-variable configuration.

## Create the schema and development sample

Run these commands from the project root in PowerShell. Enter the `todo_user`
role password when prompted:

```powershell
psql -h localhost -U todo_user -d todo_db -v ON_ERROR_STOP=1 -f database\schema.sql
psql -h localhost -U todo_user -d todo_db -v ON_ERROR_STOP=1 -f database\dev_seed.sql
```

`schema.sql` creates the types, tables, constraints, indexes, and timestamp
triggers inside a transaction. It is an initial schema, not a repeatable
migration; run it once on a new, empty database. `dev_seed.sql` is safe to
rerun. Its demo account contains an intentionally unusable password-hash
marker and cannot log in; it is only for exercising database relationships.
Do not use it as an application account.

## Verify tables, constraints, and relationships

List tables and inspect their definitions:

```powershell
psql -h localhost -U todo_user -d todo_db
```

At the `todo_app=>` prompt:

```sql
\dt
\d users
\d tasks
```

Expected tables are `users` and `tasks`. `\d tasks` should show its
`owner_id` foreign key referencing `users(id)` with `ON DELETE CASCADE`.

Verify the sample relationship and aggregate cardinality:

```sql
SELECT u.id, u.email, t.id AS task_id, t.title, t.owner_id
FROM users AS u
LEFT JOIN tasks AS t ON t.owner_id = u.id
WHERE u.email = 'demo.user@example.test';

SELECT u.id, u.email, count(t.id) AS task_count
FROM users AS u
LEFT JOIN tasks AS t ON t.owner_id = u.id
GROUP BY u.id, u.email;
```

The first query should return the demo user and its sample task; the task's
`owner_id` must equal the user's `id`. The second query should return each user
with a count of their tasks.

Check that case-insensitive duplicate emails and orphan tasks are rejected:

```sql
INSERT INTO users (full_name, email, password_hash)
VALUES ('Duplicate', ' DEMO.USER@EXAMPLE.TEST ', 'test-only');
```

Expected: a unique-constraint violation. This statement does not change the
database. To verify the owner constraint without leaving test data, use a
transaction and roll it back:

```sql
BEGIN;
INSERT INTO tasks (title, owner_id) VALUES ('Orphan test', -1);
ROLLBACK;
```

Expected: a foreign-key violation; issue `ROLLBACK` if `psql` reports the
transaction is aborted. In `psql`, exit with `\q`.

## Phase checklist

- [x] Define users/tasks tables, keys, constraints, indexes, and deletion behavior.
- [x] Add repeatable development-only sample data without usable credentials.
- [x] Document database setup and relationship verification.
- [ ] Create the database and run the verification queries locally.
- [ ] Resolve any setup errors and confirm Phase 1 before beginning Phase 2.
