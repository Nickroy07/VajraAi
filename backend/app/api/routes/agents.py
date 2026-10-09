"""Agent listing route."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.database.init_db import get_connection
from app.schemas.agent import AgentList, AgentResponse

router = APIRouter(prefix="/api/v1", tags=["agents"])


@router.get("/agents", response_model=AgentList)
def list_agents() -> AgentList:
    settings = get_settings()
    conn = get_connection(settings.sqlite_path)
    try:
        rows = conn.execute("SELECT * FROM agents ORDER BY registered_at DESC").fetchall()
        agents = [
            AgentResponse(
                agent_id=r["agent_id"],
                name=r["name"],
                agent_type=r["agent_type"],
                status=r["status"],
                registered_at=r["registered_at"],
            )
            for r in rows
        ]
        return AgentList(agents=agents, count=len(agents))
    finally:
        conn.close()