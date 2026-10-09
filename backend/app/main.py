from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.database.init_db import initialize_sqlite

settings = get_settings()
app = FastAPI(title="VAJRA AI Gateway", version="0.1.0")


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
