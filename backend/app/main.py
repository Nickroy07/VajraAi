from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.api.routes.overview import router as overview_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.agents import router as agents_router
from app.api.routes.policies import router as policies_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.gateway import router as gateway_router
from app.api.routes.events import router as events_router
from app.api.routes.attack_lab import router as attack_lab_router
from app.core.config import get_settings
from app.database.init_db import initialize_sqlite

settings = get_settings()
app = FastAPI(title="VAJRA AI Gateway", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    initialize_sqlite(settings.sqlite_path)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "http_error",
                "message": str(exc.detail),
                "details": {},
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_error",
                "message": "An unexpected error occurred",
                "details": {"exception": exc.__class__.__name__},
            }
        },
    )


app.include_router(health_router)
app.include_router(overview_router)
app.include_router(tasks_router)
app.include_router(agents_router)
app.include_router(policies_router)
app.include_router(approvals_router)
app.include_router(gateway_router)
app.include_router(events_router)
app.include_router(attack_lab_router)