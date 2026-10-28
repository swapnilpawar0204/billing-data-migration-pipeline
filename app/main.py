import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app import __version__
from app.api.routes import router
from app.utils.logger import get_logger, request_id_var

logger = get_logger(__name__)

app = FastAPI(
    title="Billing Data Migration Pipeline",
    description="Billing transaction ingestion, migration, and reconciliation API.",
    version=__version__,
)

app.include_router(router)

_MAX_REQUEST_ID_LENGTH = 64


@app.middleware("http")
async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Attach a correlation ID to every request, log line and response."""
    incoming = request.headers.get("X-Request-ID", "").strip()
    request_id = (
        incoming[:_MAX_REQUEST_ID_LENGTH]
        if incoming.isprintable() and incoming
        else uuid.uuid4().hex
    )
    token = request_id_var.set(request_id)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Return a safe response for database errors without exposing internals."""
    logger.error("Unhandled database error: %s", exc.__class__.__name__)
    return JSONResponse(
        status_code=503,
        content={"detail": "Database service is unavailable"},
    )
