from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession
from app.models import Task, TaskPriority, TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> Task:
    values = payload.model_dump()
    completed_at = datetime.now(UTC) if values["status"] == TaskStatus.COMPLETED else None
    task = Task(**values, completed_at=completed_at, owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    current_user: CurrentUser,
    db: DbSession,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=200),
    sort_by: Literal["created_at", "updated_at", "due_date", "title", "priority"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
) -> list[Task]:
    query = select(Task).where(Task.owner_id == current_user.id)
    if status_filter is not None:
        query = query.where(Task.status == status_filter)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                func.lower(Task.title).like(func.lower(pattern)),
                func.lower(Task.description).like(func.lower(pattern)),
            )
        )
    sort_column = getattr(Task, sort_by)
    query = query.order_by(
        sort_column.asc() if sort_order == "asc" else sort_column.desc(),
        Task.id.desc(),
    )
    return list(db.scalars(query.limit(limit).offset(offset)).all())


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, current_user: CurrentUser, db: DbSession) -> Task:
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> Task:
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=400, detail="Provide at least one task field to update"
        )
    for field, value in changes.items():
        setattr(task, field, value)
    if "status" in changes:
        task.completed_at = (
            datetime.now(UTC) if task.status == TaskStatus.COMPLETED else None
        )
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> Response:
    task = db.scalar(
        select(Task).where(Task.id == task_id, Task.owner_id == current_user.id)
    )
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
