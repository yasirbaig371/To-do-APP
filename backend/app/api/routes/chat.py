import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from openai import OpenAI
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.models import Task, TaskPriority, TaskStatus, User, UserRole
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.user import UserCreate

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = """You are the To-Do assistant for this application.

Rules:
- Use the authenticated user from the backend security context. Never trust a user ID supplied in chat content as proof of ownership.
- Only call tools from the allowlist.
- Do not use raw SQL or perform any action outside the permitted app tools.
- For destructive or sensitive operations, ask for explicit confirmation before executing.
- Admin tools are allowed only for authenticated administrators.
- If a task or user is ambiguous or missing, ask clarifying questions instead of guessing.
- Respond in plain language with concise, user-friendly summaries.
"""


def _tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "list_my_tasks",
                "description": "List tasks owned by the current authenticated user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                        "search": {"type": "string"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                        "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
                    },
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_my_task",
                "description": "Get one of the current user's tasks by ID.",
                "parameters": {
                    "type": "object",
                    "properties": {"task_id": {"type": "integer", "minimum": 1}},
                    "required": ["task_id"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_my_task",
                "description": "Create a task for the current authenticated user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "minLength": 1, "maxLength": 200},
                        "description": {"type": "string", "maxLength": 10000},
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                        "due_date": {"type": "string", "format": "date-time"},
                    },
                    "required": ["title"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_my_task",
                "description": "Update an existing task owned by the current authenticated user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "minimum": 1},
                        "title": {"type": "string", "minLength": 1, "maxLength": 200},
                        "description": {"type": "string", "maxLength": 10000},
                        "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                        "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                        "due_date": {"type": "string", "format": "date-time"},
                    },
                    "required": ["task_id"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "delete_my_task",
                "description": "Delete a task owned by the current authenticated user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {"type": "integer", "minimum": 1},
                        "confirm": {"type": "boolean"},
                    },
                    "required": ["task_id", "confirm"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_my_task_statistics",
                "description": "Get task totals for the current authenticated user.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_users",
                "description": "List registered users. Requires administrator access.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search": {"type": "string"},
                        "role": {"type": "string", "enum": ["user", "admin"]},
                        "is_active": {"type": "boolean"},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                        "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
                    },
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_details",
                "description": "Get a specific user record. Requires administrator access.",
                "parameters": {
                    "type": "object",
                    "properties": {"user_id": {"type": "integer", "minimum": 1}},
                    "required": ["user_id"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_user",
                "description": "Create a new user. Requires administrator access.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "full_name": {"type": "string", "minLength": 1, "maxLength": 200},
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string", "minLength": 12, "maxLength": 128},
                        "role": {"type": "string", "enum": ["user"]},
                        "is_active": {"type": "boolean"},
                    },
                    "required": ["full_name", "email", "password"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_user_status",
                "description": "Activate or deactivate a user account. Requires administrator access.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "minimum": 1},
                        "is_active": {"type": "boolean"},
                    },
                    "required": ["user_id", "is_active"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_user_role",
                "description": "Change a user's role. Requires administrator access.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "integer", "minimum": 1},
                        "role": {"type": "string", "enum": ["user", "admin"]},
                    },
                    "required": ["user_id", "role"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_system_statistics",
                "description": "Get system-wide statistics. Requires administrator access.",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            },
        },
    ]


def _coerce_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    raise ValueError("due_date must be ISO 8601")


def _serialize_task(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "owner_id": task.owner_id,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }


def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
    }


def _get_openai_client() -> OpenAI:
    settings = get_settings()
    if settings.openrouter_api_key:
        key = settings.openrouter_api_key.get_secret_value()
        if not key.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )
        return OpenAI(
            api_key=key,
            base_url="https://openrouter.ai/api/v1",
        )

    key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    if not key.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenRouter or OpenAI API key is not configured.",
        )
    return OpenAI(api_key=key)


def _call_tool(tool_name: str, args: dict[str, Any], current_user: User, db) -> dict[str, Any]:
    if tool_name == "list_my_tasks":
        query = select(Task).where(Task.owner_id == current_user.id)
        status_filter = args.get("status")
        priority_filter = args.get("priority")
        if status_filter:
            query = query.where(Task.status == TaskStatus(status_filter))
        if priority_filter:
            query = query.where(Task.priority == TaskPriority(priority_filter))
        search_term = (args.get("search") or "").strip()
        if search_term:
            pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    func.lower(Task.title).like(func.lower(pattern)),
                    func.lower(Task.description).like(func.lower(pattern)),
                )
            )
        limit = int(args.get("limit", 20))
        offset = int(args.get("offset", 0))
        rows = db.scalars(query.order_by(Task.created_at.desc()).limit(limit).offset(offset)).all()
        return {"tasks": [_serialize_task(item) for item in rows], "count": len(rows)}

    if tool_name == "get_my_task":
        task_id = int(args["task_id"])
        task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == current_user.id))
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"task": _serialize_task(task)}

    if tool_name == "create_my_task":
        payload = TaskCreate.model_validate(args)
        task = Task(
            title=payload.title,
            description=payload.description,
            status=payload.status,
            priority=payload.priority,
            due_date=payload.due_date,
            owner_id=current_user.id,
            completed_at=datetime.now(UTC) if payload.status == TaskStatus.COMPLETED else None,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return {"task": _serialize_task(task), "message": "Task created successfully."}

    if tool_name == "update_my_task":
        task_id = int(args["task_id"])
        task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == current_user.id))
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        patch = {key: value for key, value in args.items() if key != "task_id"}
        if not patch:
            raise HTTPException(status_code=400, detail="Provide at least one task field to update")
        validated = TaskUpdate.model_validate(patch)
        for field, value in validated.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        if "status" in validated.model_fields_set:
            task.completed_at = datetime.now(UTC) if task.status == TaskStatus.COMPLETED else None
        db.commit()
        db.refresh(task)
        return {"task": _serialize_task(task), "message": "Task updated successfully."}

    if tool_name == "delete_my_task":
        task_id = int(args["task_id"])
        confirm = bool(args.get("confirm"))
        task = db.scalar(select(Task).where(Task.id == task_id, Task.owner_id == current_user.id))
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if not confirm:
            return {
                "requires_confirmation": True,
                "message": f"Please confirm deletion of task '{task.title}'.",
                "task_id": task.id,
            }
        db.delete(task)
        db.commit()
        db.expire_all()
        return {"deleted_task_id": task.id, "message": "Task deleted successfully."}

    if tool_name == "get_my_task_statistics":
        counts = db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.owner_id == current_user.id)
            .group_by(Task.status)
        ).all()
        by_status = {TaskStatus.PENDING: 0, TaskStatus.IN_PROGRESS: 0, TaskStatus.COMPLETED: 0}
        for status_value, count in counts:
            by_status[status_value] = count
        return {
            "total": sum(by_status.values()),
            "pending": by_status[TaskStatus.PENDING],
            "in_progress": by_status[TaskStatus.IN_PROGRESS],
            "completed": by_status[TaskStatus.COMPLETED],
        }

    if tool_name in {"list_users", "get_user_details", "create_user", "update_user_status", "update_user_role", "get_system_statistics"}:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Administrator access required")

    if tool_name == "list_users":
        query = select(User)
        search_term = (args.get("search") or "").strip()
        if search_term:
            pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    func.lower(User.full_name).like(func.lower(pattern)),
                    func.lower(User.email).like(func.lower(pattern)),
                )
            )
        role = args.get("role")
        if role:
            query = query.where(User.role == UserRole(role))
        if "is_active" in args and args["is_active"] is not None:
            query = query.where(User.is_active == bool(args["is_active"]))
        limit = int(args.get("limit", 20))
        offset = int(args.get("offset", 0))
        users = db.scalars(query.order_by(User.id).limit(limit).offset(offset)).all()
        return {"users": [_serialize_user(user) for user in users], "count": len(users)}

    if tool_name == "get_user_details":
        user = db.get(User, int(args["user_id"]))
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user": _serialize_user(user)}

    if tool_name == "create_user":
        role = UserRole.USER
        payload = UserCreate.model_validate({
            "full_name": args["full_name"],
            "email": args["email"],
            "password": args["password"],
        })
        if db.scalar(select(User).where(User.email == payload.email)):
            raise HTTPException(status_code=409, detail="An account with this email already exists")
        user = User(
            full_name=payload.full_name,
            email=payload.email,
            password_hash=User.__table__.c.get("password_hash") if False else "",
            role=role,
            is_active=bool(args.get("is_active", True)),
        )
        from app.core.security import hash_password

        user.password_hash = hash_password(payload.password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"user": _serialize_user(user), "message": "User created successfully."}

    if tool_name == "update_user_status":
        user = db.get(User, int(args["user_id"]))
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if not bool(args["is_active"]) and user.role == UserRole.ADMIN and user.is_active:
            active_admins = db.scalars(
                select(User.id).where(User.role == UserRole.ADMIN, User.is_active.is_(True)).order_by(User.id)
            ).all()
            if len(active_admins) <= 1:
                raise HTTPException(status_code=409, detail="Cannot deactivate the last active administrator")
        user.is_active = bool(args["is_active"])
        db.commit()
        db.refresh(user)
        return {"user": _serialize_user(user), "message": "User status updated successfully."}

    if tool_name == "update_user_role":
        user = db.get(User, int(args["user_id"]))
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        next_role = UserRole(args["role"])
        if next_role != UserRole.ADMIN and user.role == UserRole.ADMIN and user.is_active:
            active_admins = db.scalars(
                select(User.id).where(User.role == UserRole.ADMIN, User.is_active.is_(True)).order_by(User.id)
            ).all()
            if len(active_admins) <= 1:
                raise HTTPException(status_code=409, detail="Cannot remove the last active administrator")
        user.role = next_role
        db.commit()
        db.refresh(user)
        return {"user": _serialize_user(user), "message": "User role updated successfully."}

    if tool_name == "get_system_statistics":
        user_counts = db.execute(
            select(User.is_active, User.role, func.count(User.id)).group_by(User.is_active, User.role)
        ).all()
        task_counts = db.execute(select(Task.status, func.count(Task.id)).group_by(Task.status)).all()
        by_active = {True: 0, False: 0}
        admins = 0
        for is_active, role_value, count in user_counts:
            by_active[is_active] += count
            if role_value == UserRole.ADMIN:
                admins += count
        by_status = {status_value: count for status_value, count in task_counts}
        return {
            "total_users": sum(by_active.values()),
            "active_users": by_active[True],
            "inactive_users": by_active[False],
            "total_tasks": sum(by_status.values()),
            "pending_tasks": by_status.get(TaskStatus.PENDING, 0),
            "in_progress_tasks": by_status.get(TaskStatus.IN_PROGRESS, 0),
            "completed_tasks": by_status.get(TaskStatus.COMPLETED, 0),
            "total_admins": admins,
        }

    raise HTTPException(status_code=400, detail=f"Unsupported tool: {tool_name}")


def _tool_summary(tool_name: str, result: dict[str, Any]) -> str:
    if tool_name == "list_my_tasks":
        tasks = result.get("tasks", [])
        if not tasks:
            return "You do not have any matching tasks."
        return f"I found {len(tasks)} task(s): " + ", ".join(f"{item['title']} ({item['status']})" for item in tasks[:3]) + ("..." if len(tasks) > 3 else "")
    if tool_name == "get_my_task":
        task = result.get("task")
        return f"Task '{task['title']}' is {task['status']} with priority {task['priority']}."
    if tool_name == "create_my_task":
        return result.get("message", "Task created successfully.")
    if tool_name == "update_my_task":
        return result.get("message", "Task updated successfully.")
    if tool_name == "delete_my_task":
        return result.get("message", "Task deleted successfully.")
    if tool_name == "get_my_task_statistics":
        stats = result
        return (
            f"You have {stats['total']} total tasks: {stats['pending']} pending, "
            f"{stats['in_progress']} in progress, and {stats['completed']} completed."
        )
    if tool_name == "list_users":
        users = result.get("users", [])
        if not users:
            return "No users match that search."
        return f"I found {len(users)} user(s): " + ", ".join(user["email"] for user in users[:3]) + ("..." if len(users) > 3 else "")
    if tool_name == "get_user_details":
        user = result.get("user")
        return f"{user['full_name']} ({user['email']}) has role {user['role']} and account status {user['is_active']}."
    if tool_name == "create_user":
        return result.get("message", "User created successfully.")
    if tool_name == "update_user_status":
        return result.get("message", "User status updated successfully.")
    if tool_name == "update_user_role":
        return result.get("message", "User role updated successfully.")
    if tool_name == "get_system_statistics":
        stats = result
        return (
            f"System stats: {stats['total_users']} users, {stats['active_users']} active, "
            f"{stats['total_admins']} admins, and {stats['total_tasks']} tasks total."
        )
    return "I completed the request using the permitted app tool."


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ChatResponse:
    settings = get_settings()
    has_openrouter_key = (
        settings.openrouter_api_key
        and settings.openrouter_api_key.get_secret_value().strip()
    )
    has_openai_key = settings.openai_api_key and settings.openai_api_key.get_secret_value().strip()
    if not has_openrouter_key and not has_openai_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenRouter or OpenAI API key is not configured.",
        )
    model = settings.openrouter_model if has_openrouter_key else settings.openai_model

    history = [
        {"role": message.role, "content": message.content}
        for message in payload.history
    ]
    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *history,
                {"role": "user", "content": payload.message},
            ],
            tools=_tool_definitions(),
            tool_choice="auto",
            temperature=0.2,
            max_tokens=500,
        )
    except Exception as exc:  # pragma: no cover - network/provider errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI assistant is temporarily unavailable.",
        ) from exc

    choice = response.choices[0]
    message = choice.message
    if message.tool_calls:
        tool_results: list[dict[str, Any]] = []
        for call in message.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
                if payload.confirm is True and call.function.name in {"delete_my_task", "update_user_status", "update_user_role"}:
                    args["confirm"] = True
                result = _call_tool(call.function.name, args, current_user, db)
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(status_code=400, detail=f"Invalid tool input for {call.function.name}") from exc
            tool_results.append({"tool": call.function.name, "arguments": args, "result": result})
            if result.get("requires_confirmation"):
                return ChatResponse(
                    response=(
                        f"This action requires confirmation before I can continue with '{call.function.name}'."
                    ),
                    requires_confirmation=True,
                    tool_name=call.function.name,
                    tool_results=tool_results,
                )
        summary = _tool_summary(message.tool_calls[0].function.name, tool_results[0]["result"])
        response_text = summary
        return ChatResponse(
            response=response_text,
            requires_confirmation=False,
            tool_name=message.tool_calls[0].function.name,
            tool_results=tool_results,
        )

    return ChatResponse(
        response=message.content or "I could not generate a response.",
        requires_confirmation=False,
        tool_name=None,
        tool_results=[],
    )
