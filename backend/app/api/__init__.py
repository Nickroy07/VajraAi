"""API routes for the VAJRA AI Gateway."""

from app.api.routes.health import router as health_router
from app.api.routes.overview import router as overview_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.agents import router as agents_router
from app.api.routes.policies import router as policies_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.gateway import router as gateway_router
from app.api.routes.events import router as events_router
from app.api.routes.attack_lab import router as attack_lab_router
from app.api.routes.document_guard import router as document_guard_router

__all__ = [
    "health_router",
    "overview_router",
    "tasks_router",
    "agents_router",
    "policies_router",
    "approvals_router",
    "gateway_router",
    "events_router",
    "attack_lab_router",
    "document_guard_router",
]