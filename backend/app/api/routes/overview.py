"""Overview endpoint — returns demo-mode summary with derived counts."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.services.gateway import get_gateway

router = APIRouter(prefix="/api/v1", tags=["overview"])


@router.get("/overview")
def get_overview() -> dict:
    settings = get_settings()
    gateway = get_gateway(settings.sqlite_path)
    return gateway.get_overview()