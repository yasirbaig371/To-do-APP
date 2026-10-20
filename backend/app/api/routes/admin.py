from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import AdminUser, DbSession
from app.models import Task, TaskStatus, User, UserRole
from app.schemas.user import (
    AdminStatistics,
    AdminUserRead,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    UserRead,
)

router = APIRouter(prefix="/admin", tags=["administration"])


def _lock_active_admin_ids(db: DbSession) -> list[int]:
    return list(
        db.scalars(
            select(User.id)
            .where(User.role == UserRole.ADMIN, User.is_active.is_(True))
            .order_by(User.id)
            .with_for_update()
        )
    )


@router.get("/users", response_model=list[AdminUserRead])
def list_users(
    admin: AdminUser,
    db: DbSession,
    search: str | None = Query(default=None, min_length=1, max_length=200),
    role: UserRole | None = None,
    is_active: bool | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=100000),
) -> list[AdminUserRead]:
    del admin
    query = select(User, func.count(Task.id).label("task_count")).outerjoin(
        Task, Task.owner_id == User.id
    )
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            or_(
                func.lower(User.full_name).like(func.lower(pattern)),
                func.lower(User.email).like(func.lower(pattern)),
            )
        )
    if role is not None:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    rows = db.execute(
        query.group_by(User.id).order_by(User.id).limit(limit).offset(offset)
    ).all()
    return [
        AdminUserRead.model_validate(user).model_copy(update={"task_count": count})
        for user, count in rows
    ]


@router.get("/users/{user_id}", response_model=AdminUserRead)
def get_user(
    user_id: int,
    admin: AdminUser,
    db: DbSession,
) -> AdminUserRead:
    del admin
    row = db.execute(
        select(User, func.count(Task.id).label("task_count"))
        .outerjoin(Task, Task.owner_id == User.id)
        .where(User.id == user_id)
        .group_by(User.id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    user, task_count = row
    return AdminUserRead.model_validate(user).model_copy(
        update={"task_count": task_count}
    )


@router.patch("/users/{user_id}/status", response_model=UserRead)
def update_user_status(
    user_id: int,
    payload: AdminUserStatusUpdate,
    admin: AdminUser,
    db: DbSession,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.is_active and user.role == UserRole.ADMIN and user.is_active:
        if len(_lock_active_admin_ids(db)) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot deactivate the last active administrator",
            )
    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/role", response_model=UserRead)
def update_user_role(
    user_id: int,
    payload: AdminUserRoleUpdate,
    admin: AdminUser,
    db: DbSession,
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role != UserRole.ADMIN and user.role == UserRole.ADMIN and user.is_active:
        if len(_lock_active_admin_ids(db)) <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot remove the last active administrator",
            )
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/statistics", response_model=AdminStatistics)
def get_admin_statistics(admin: AdminUser, db: DbSession) -> AdminStatistics:
    del admin
    user_counts = db.execute(
        select(User.is_active, User.role, func.count(User.id)).group_by(
            User.is_active, User.role
        )
    ).all()
    task_counts = db.execute(
        select(Task.status, func.count(Task.id)).group_by(Task.status)
    ).all()
    by_active = {active: 0 for active in (True, False)}
    admins = 0
    for active, role_value, count in user_counts:
        by_active[active] += count
        if role_value == UserRole.ADMIN:
            admins += count
    by_status = {task_status: count for task_status, count in task_counts}
    return AdminStatistics(
        total_users=sum(by_active.values()),
        active_users=by_active[True],
        inactive_users=by_active[False],
        total_tasks=sum(by_status.values()),
        pending_tasks=by_status.get(TaskStatus.PENDING, 0),
        in_progress_tasks=by_status.get(TaskStatus.IN_PROGRESS, 0),
        completed_tasks=by_status.get(TaskStatus.COMPLETED, 0),
        total_admins=admins,
    )
