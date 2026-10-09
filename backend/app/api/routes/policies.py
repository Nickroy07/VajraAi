"""Policy routes — inspect and update task policy."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.database.init_db import get_connection
from app.schemas.policy import PolicyResponse, PolicyRule, PolicyUpdate

router = APIRouter(prefix="/api/v1", tags=["policies"])


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("/tasks/{task_id}/policy", response_model=PolicyResponse)
def get_policy(task_id: str) -> PolicyResponse:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    try:
        task = conn.execute("SELECT task_id FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        row = conn.execute("SELECT * FROM policies WHERE task_id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No policy found for this task")

        rules_raw = row["rules"]
        rules_data = json.loads(rules_raw) if isinstance(rules_raw, str) else rules_raw
        rules = [PolicyRule(**r) for r in rules_data]
        return PolicyResponse(
            policy_id=row["policy_id"],
            task_id=row["task_id"],
            rules=rules,
            updated_at=row["updated_at"],
        )
    finally:
        conn.close()


@router.put("/tasks/{task_id}/policy", response_model=PolicyResponse)
def update_policy(task_id: str, body: PolicyUpdate) -> PolicyResponse:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    now = _utcnow()
    try:
        task = conn.execute("SELECT task_id FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        row = conn.execute("SELECT * FROM policies WHERE task_id = ?", (task_id,)).fetchone()

        rules_json = json.dumps([r.model_dump() if hasattr(r, "model_dump") else r for r in body.rules])

        if not row:
            # Auto-create policy for new tasks
            from uuid import uuid4
            policy_id = str(uuid4())
            conn.execute(
                "INSERT INTO policies (policy_id, task_id, rules, updated_at) VALUES (?, ?, ?, ?)",
                (policy_id, task_id, rules_json, now),
            )
            conn.commit()
            return PolicyResponse(
                policy_id=policy_id,
                task_id=task_id,
                rules=body.rules,
                updated_at=now,
            )

        conn.execute(
            "UPDATE policies SET rules = ?, updated_at = ? WHERE task_id = ?",
            (rules_json, now, task_id),
        )
        conn.commit()

        return PolicyResponse(
            policy_id=row["policy_id"],
            task_id=task_id,
            rules=body.rules,
            updated_at=now,
        )
    finally:
        conn.close()