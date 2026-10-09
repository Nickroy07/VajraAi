"""Event routes — filterable event listing with pagination."""

import json

from fastapi import APIRouter, HTTPException, Query

from app.core.config import get_settings
from app.database.init_db import get_connection
from app.schemas.event import EventList, EventResponse

router = APIRouter(prefix="/api/v1", tags=["events"])


@router.get("/events", response_model=EventList)
def list_events(
    authorization: str | None = Query(None, description="Filter: allowed | denied"),
    execution_status: str | None = Query(None, description="Filter: not_attempted | succeeded | failed"),
    task_id: str | None = Query(None),
    tool_name: str | None = Query(None),
    agent_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> EventList:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    try:
        query = "SELECT * FROM events WHERE 1=1"
        params: list = []

        if authorization:
            query += " AND authorization = ?"
            params.append(authorization)
        if execution_status:
            query += " AND execution_status = ?"
            params.append(execution_status)
        if task_id:
            query += " AND task_id = ?"
            params.append(task_id)
        if tool_name:
            query += " AND tool_name = ?"
            params.append(tool_name)
        if agent_id:
            query += " AND agent_id = ?"
            params.append(agent_id)

        # Total count
        count_row = conn.execute(
            query.replace("SELECT *", "SELECT COUNT(*)"), params
        ).fetchone()
        total = count_row[0] if count_row else 0

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        events = []
        for r in rows:
            args_raw = r["arguments"]
            details_raw = r["details"]
            events.append(EventResponse(
                event_id=r["event_id"],
                task_id=r["task_id"],
                agent_id=r["agent_id"],
                tool_name=r["tool_name"],
                event_type=r["event_type"],
                authorization=r["authorization"],
                authorization_reason=r["authorization_reason"] or "",
                execution_status=r["execution_status"],
                execution_result=r["execution_result"],
                arguments=json.loads(args_raw) if isinstance(args_raw, str) else (args_raw if isinstance(args_raw, dict) else {}),
                resource=r["resource"] or "",
                destination=r["destination"] or "",
                timestamp=r["timestamp"],
                details=json.loads(details_raw) if isinstance(details_raw, str) else (details_raw if isinstance(details_raw, dict) else {}),
            ))
        return EventList(events=events, count=total)
    finally:
        conn.close()


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: str) -> EventResponse:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    try:
        r = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
        if not r:
            raise HTTPException(status_code=404, detail="Event not found")
        args_raw = r["arguments"]
        details_raw = r["details"]
        return EventResponse(
            event_id=r["event_id"],
            task_id=r["task_id"],
            agent_id=r["agent_id"],
            tool_name=r["tool_name"],
            event_type=r["event_type"],
            authorization=r["authorization"],
            authorization_reason=r["authorization_reason"] or "",
            execution_status=r["execution_status"],
            execution_result=r["execution_result"],
            arguments=json.loads(args_raw) if isinstance(args_raw, str) else (args_raw if isinstance(args_raw, dict) else {}),
            resource=r["resource"] or "",
            destination=r["destination"] or "",
            timestamp=r["timestamp"],
            details=json.loads(details_raw) if isinstance(details_raw, str) else (details_raw if isinstance(details_raw, dict) else {}),
        )
    finally:
        conn.close()