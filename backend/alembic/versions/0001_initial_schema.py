"""Create the initial users and tasks schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("user", "admin", name="user_role", create_type=False)
task_status = postgresql.ENUM(
    "pending", "in_progress", "completed", name="task_status", create_type=False
)
task_priority = postgresql.ENUM(
    "low", "medium", "high", name="task_priority", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    task_status.create(bind, checkfirst=True)
    task_priority.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, server_default=sa.text("'user'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("length(btrim(full_name)) > 0", name="users_full_name_not_blank"),
        sa.CheckConstraint("length(btrim(email)) > 0", name="users_email_not_blank"),
        sa.CheckConstraint("length(password_hash) > 0", name="users_password_hash_not_blank"),
    )
    op.create_index(
        "users_email_case_insensitive_unique",
        "users",
        [sa.text("lower(btrim(email))")],
        unique=True,
    )

    op.create_table(
        "tasks",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status", task_status, server_default=sa.text("'pending'"), nullable=False
        ),
        sa.Column(
            "priority", task_priority, server_default=sa.text("'medium'"), nullable=False
        ),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("length(btrim(title)) > 0", name="tasks_title_not_blank"),
        sa.CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name="tasks_completion_timestamp_consistent",
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "tasks_owner_created_idx",
        "tasks",
        ["owner_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index(
        "tasks_owner_status_created_idx",
        "tasks",
        ["owner_id", "status", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index(
        "tasks_owner_priority_created_idx",
        "tasks",
        ["owner_id", "priority", sa.text("created_at DESC"), sa.text("id DESC")],
    )
    op.create_index(
        "tasks_due_date_idx",
        "tasks",
        ["due_date"],
        postgresql_where=sa.text("due_date IS NOT NULL"),
    )
    op.execute(
        """
        CREATE FUNCTION set_updated_at()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$;
        """
    )
    op.execute(
        "CREATE TRIGGER users_set_updated_at BEFORE UPDATE ON users "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )
    op.execute(
        "CREATE TRIGGER tasks_set_updated_at BEFORE UPDATE ON tasks "
        "FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tasks_set_updated_at ON tasks")
    op.execute("DROP TRIGGER IF EXISTS users_set_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
    op.drop_table("tasks")
    op.drop_index("users_email_case_insensitive_unique", table_name="users")
    op.drop_table("users")
    task_priority.drop(op.get_bind(), checkfirst=True)
    task_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
