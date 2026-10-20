from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, DbSession
from app.core.security import hash_password, verify_password
from app.models import Task, TaskStatus, User
from app.schemas.user import (
    ChangePasswordRequest,
    UserProfileUpdate,
    UserRead,
    UserTaskStatistics,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: CurrentUser) -> User:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_my_profile(
    payload: UserProfileUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> User:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one profile field to update",
        )
    for field, value in changes.items():
        if value is not None:
            setattr(current_user, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from exc
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from current password",
        )
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()


@router.get("/me/statistics", response_model=UserTaskStatistics)
def my_task_statistics(current_user: CurrentUser, db: DbSession) -> UserTaskStatistics:
    rows = db.execute(
        select(Task.status, func.count(Task.id))
        .where(Task.owner_id == current_user.id)
        .group_by(Task.status)
    ).all()
    counts = {status_value: count for status_value, count in rows}
    return UserTaskStatistics(
        total=sum(counts.values()),
        pending=counts.get(TaskStatus.PENDING, 0),
        in_progress=counts.get(TaskStatus.IN_PROGRESS, 0),
        completed=counts.get(TaskStatus.COMPLETED, 0),
    )
