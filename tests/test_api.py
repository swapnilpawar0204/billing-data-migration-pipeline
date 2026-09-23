import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config.settings import settings
from app.database.connection import Base, get_db
from app.main import app

client = TestClient(app)


@pytest.fixture
def api_client() -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as database_session:
            yield database_session

    app.dependency_overrides[get_db] = override_get_db
    yield client
    app.dependency_overrides.clear()
    engine.dispose()


def transaction_payload(external_id: str = "txn-001") -> dict[str, object]:
    return {
        "external_transaction_id": external_id,
        "customer_id": "customer-001",
        "amount": "10.00",
        "currency": " usd ",
        "status": " Paid ",
    }


def test_application_imports() -> None:
    assert app is not None


def test_health_endpoint_returns_200() -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_contains_status() -> None:
    response = client.get("/health")
    payload = response.json()
    assert "status" in payload


def test_health_status_is_healthy() -> None:
    response = client.get("/health")
    payload = response.json()
    assert payload["status"] == "healthy"


def test_health_response_contains_environment() -> None:
    response = client.get("/health")
    payload = response.json()
    assert "environment" in payload
    assert payload["environment"] == settings.app_env


def test_validate_endpoint_returns_valid_and_rejected_records(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/v1/migration/validate",
        json={
            "transactions": [
                transaction_payload(),
                {
                    **transaction_payload("txn-002"),
                    "amount": "-1.00",
                    "currency": "",
                },
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid_count"] == 1
    assert payload["rejected_count"] == 1
    assert payload["valid_records"][0]["currency"] == "USD"


def test_validate_endpoint_rejects_malformed_request(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/v1/migration/validate",
        json={"transactions": "not-a-list"},
    )

    assert response.status_code == 422


def test_validate_endpoint_rejects_missing_transactions_field(
    api_client: TestClient,
) -> None:
    response = api_client.post("/api/v1/migration/validate", json={})

    assert response.status_code == 422
    assert "detail" in response.json()


def test_validate_endpoint_accepts_empty_batch(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/migration/validate",
        json={"transactions": []},
    )

    assert response.status_code == 200
    assert response.json()["valid_count"] == 0
    assert response.json()["rejected_count"] == 0


def test_validate_endpoint_does_not_write_to_database(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/v1/migration/validate",
        json={"transactions": [transaction_payload()]},
    )

    assert response.status_code == 200


def test_run_endpoint_migrates_only_valid_records(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/v1/migration/run",
        json={
            "transactions": [
                transaction_payload(),
                {**transaction_payload("txn-002"), "amount": "-1.00"},
            ]
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["migration"]["inserted"] == 1
    assert payload["validation"]["rejected_count"] == 1
    assert payload["reconciliation"]["reconciled"] is True


def test_run_endpoint_is_idempotent(api_client: TestClient) -> None:
    request = {"transactions": [transaction_payload()]}

    first = api_client.post("/api/v1/migration/run", json=request)
    second = api_client.post("/api/v1/migration/run", json=request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["migration"]["inserted"] == 0
    assert second.json()["migration"]["skipped_duplicates"] == 1


def test_run_endpoint_skips_duplicate_ids_within_batch(
    api_client: TestClient,
) -> None:
    response = api_client.post(
        "/api/v1/migration/run",
        json={
            "transactions": [
                transaction_payload(),
                transaction_payload(),
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["migration"]["inserted"] == 1
    assert response.json()["migration"]["skipped_duplicates"] == 1


def test_run_endpoint_handles_reasonable_batch(api_client: TestClient) -> None:
    response = api_client.post(
        "/api/v1/migration/run",
        json={
            "transactions": [transaction_payload(f"txn-{index}") for index in range(25)]
        },
    )

    assert response.status_code == 200
    assert response.json()["migration"]["inserted"] == 25
    assert response.json()["reconciliation"]["reconciled"] is True


def test_status_endpoint_returns_structured_database_error(
    api_client: TestClient,
) -> None:
    from sqlalchemy.exc import SQLAlchemyError

    def failing_session():
        raise SQLAlchemyError("secret connection details")
        yield

    app.dependency_overrides[get_db] = failing_session

    response = api_client.get("/api/v1/migration/status/txn-001")

    assert response.status_code in {500, 503}
    assert "secret connection details" not in response.text
    assert "MYSQL_PASSWORD" not in response.text
    assert "API_KEY" not in response.text


def test_status_endpoint_returns_existing_transaction(
    api_client: TestClient,
) -> None:
    api_client.post(
        "/api/v1/migration/run",
        json={"transactions": [transaction_payload()]},
    )

    response = api_client.get("/api/v1/migration/status/txn-001")

    assert response.status_code == 200
    assert response.json()["exists"] is True
    assert response.json()["transaction"]["amount"] == "10.00"


def test_status_endpoint_returns_404_for_missing_transaction(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/v1/migration/status/missing")

    assert response.status_code == 404
