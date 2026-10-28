import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config.settings import Settings, settings
from app.database.connection import Base, get_db
from app.main import app

BODY = {"transactions": []}


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override():
        with Session(engine) as s:
            yield s

    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


def test_api_is_open_when_no_key_configured(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "service_api_key", "")
    assert client.post("/api/v1/migration/validate", json=BODY).status_code == 200


def test_missing_key_is_rejected(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "service_api_key", "s3cret")
    response = client.post("/api/v1/migration/validate", json=BODY)
    assert response.status_code == 401


def test_wrong_key_is_rejected(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "service_api_key", "s3cret")
    response = client.post(
        "/api/v1/migration/run", json=BODY, headers={"X-API-Key": "nope"}
    )
    assert response.status_code == 401


def test_correct_key_is_accepted(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "service_api_key", "s3cret")
    response = client.post(
        "/api/v1/migration/run", json=BODY, headers={"X-API-Key": "s3cret"}
    )
    assert response.status_code == 200


def test_status_endpoint_requires_key(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "service_api_key", "s3cret")
    assert client.get("/api/v1/migration/status/x").status_code == 401


def test_health_does_not_require_key(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "service_api_key", "s3cret")
    monkeypatch.setattr("app.api.routes.check_database", lambda: True)
    assert client.get("/health").status_code == 200


def test_request_id_header_is_generated_and_echoed(client, monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.check_database", lambda: True)
    assert client.get("/health").headers["X-Request-ID"]
    echoed = client.get("/health", headers={"X-Request-ID": "abc-123"})
    assert echoed.headers["X-Request-ID"] == "abc-123"


def test_production_requires_secrets() -> None:
    with pytest.raises(ValidationError, match="MYSQL_PASSWORD"):
        Settings(_env_file=None, APP_ENV="production")


def test_production_accepts_complete_config() -> None:
    cfg = Settings(
        _env_file=None,
        APP_ENV="production",
        MYSQL_PASSWORD="pw",
        SERVICE_API_KEY="key",
    )
    assert cfg.is_production


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, LOG_LEVEL="LOUD")
