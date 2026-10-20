from datetime import datetime
from enum import Enum

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("length(trim(title)) > 0", name="tasks_title_not_blank"),
        CheckConstraint(
            "(status = 'completed') = (completed_at IS NOT NULL)",
            name="tasks_completion_timestamp_consistent",
        ),
        Index("tasks_owner_created_idx", "owner_id", "created_at", "id"),
        Index("tasks_owner_status_created_idx", "owner_id", "status", "created_at", "id"),
        Index(
            "tasks_owner_priority_created_idx", "owner_id", "priority", "created_at", "id"
        ),
        Index(
            "tasks_due_date_idx",
            "due_date",
            postgresql_where=text("due_date IS NOT NULL"),
            sqlite_where=text("due_date IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        SQLAlchemyEnum(
            TaskStatus,
            name="task_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=TaskStatus.PENDING,
        server_default=text("'pending'"),
    )
    priority: Mapped[TaskPriority] = mapped_column(
        SQLAlchemyEnum(
            TaskPriority,
            name="task_priority",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=text("'medium'"),
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    owner_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    owner: Mapped["User"] = relationship(back_populates="tasks")
