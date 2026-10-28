import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config.settings import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(provided: str | None = Security(_api_key_header)) -> None:
    """Authenticate callers of the migration endpoints via the X-API-Key header.

    If SERVICE_API_KEY is not configured (only permitted outside production, see
    Settings), authentication is disabled to keep local development simple.
    """
    expected = settings.service_api_key
    if not expected:
        return
    if not provided or not secrets.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
