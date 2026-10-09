"""Task CRUD routes."""

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.database.init_db import get_connection
from app.schemas.task import TaskCreate, TaskList, TaskResponse, TaskScope

router = APIRouter(prefix="/api/v1", tags=["tasks"])


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/tasks", response_model=TaskList)
def list_tasks() -> TaskList:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    try:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        tasks = []
        for r in rows:
            scope_raw = r["scope"]
            scope = json.loads(scope_raw) if isinstance(scope_raw, str) else scope_raw
            tasks.append(TaskResponse(
                task_id=r["task_id"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                status=r["status"],
                description=r["description"],
                scope=TaskScope(**scope) if isinstance(scope, dict) else scope,
            ))
        return TaskList(tasks=tasks, count=len(tasks))
    finally:
        conn.close()


@router.post("/tasks", status_code=201, response_model=TaskResponse)
def create_task(body: TaskCreate) -> TaskResponse:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    now = _utcnow()
    try:
        conn.execute(
            "INSERT INTO tasks (task_id, created_at, updated_at, status, description, scope) VALUES (?, ?, ?, ?, ?, ?)",
            (
                body.task_id,
                now,
                now,
                body.status.value if hasattr(body.status, "value") else body.status,
                body.description,
                body.scope.model_dump_json() if hasattr(body.scope, "model_dump_json") else json.dumps(body.scope),
            ),
        )
        conn.commit()
        return TaskResponse(
            task_id=body.task_id,
            created_at=now,
            updated_at=now,
            status=body.status,
            description=body.description,
            scope=body.scope,
        )
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str) -> TaskResponse:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    try:
        row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        scope_raw = row["scope"]
        scope = json.loads(scope_raw) if isinstance(scope_raw, str) else scope_raw
        return TaskResponse(
            task_id=row["task_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            status=row["status"],
            description=row["description"],
            scope=TaskScope(**scope) if isinstance(scope, dict) else scope,
        )
    finally:
        conn.close()