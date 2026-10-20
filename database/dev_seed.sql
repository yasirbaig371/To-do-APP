BEGIN;

INSERT INTO users (full_name, email, password_hash)
VALUES (
    'Demo User',
    'demo.user@example.test',
    'NOT_A_REAL_PASSWORD_HASH_DO_NOT_USE_FOR_AUTH'
)
ON CONFLICT DO NOTHING;

INSERT INTO tasks (title, description, status, priority, owner_id)
SELECT
    'Review the demo task',
    'Development-only sample data. This account cannot authenticate.',
    'pending',
    'medium',
    users.id
FROM users
WHERE lower(btrim(users.email)) = lower(btrim('demo.user@example.test'))
  AND NOT EXISTS (
      SELECT 1
      FROM tasks
      WHERE tasks.owner_id = users.id
        AND tasks.title = 'Review the demo task'
  );

COMMIT;
