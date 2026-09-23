from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import router

app = FastAPI(
    title="Cloud Billing Data Migration Pipeline",
    description="Billing transaction ingestion, migration, and reconciliation API.",
    version="0.7.0",
)

app.include_router(router)


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Return a safe response for database errors without exposing internals."""
    return JSONResponse(
        status_code=503,
        content={"detail": "Database service is unavailable"},
    )
