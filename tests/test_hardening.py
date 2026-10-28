"""Tests for retry logic, money handling, timezone storage and CLI API source."""

from datetime import datetime
from decimal import Decimal

import httpx
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import cli
from app.database.connection import Base
from app.database.models import BillingTransaction
from app.ingestion.api_client import BillingAPIClient, BillingAPIRequestError
from app.migration.migration_service import run_migration_flow
from app.transformation.transformer import transform_transaction
from app.validation.validators import validate_transactions

TXN = {
    "external_transaction_id": "txn-001",
    "customer_id": "customer-001",
    "amount": "10.00",
    "currency": "USD",
    "status": "paid",
}


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_transient_http_errors_are_retried() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json=[TXN])

    api = BillingAPIClient(client=_client(handler))

    assert len(api.fetch_raw_records()) == 1
    assert calls["n"] == 3


def test_permanent_http_errors_are_not_retried() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(401)

    api = BillingAPIClient(client=_client(handler))

    with pytest.raises(BillingAPIRequestError, match="HTTP 401"):
        api.fetch_raw_records()
    assert calls["n"] == 1


def test_retries_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.ingestion.api_client.settings.api_max_retries", 2)
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        raise httpx.ConnectError("down")

    api = BillingAPIClient(client=_client(handler))

    with pytest.raises(BillingAPIRequestError):
        api.fetch_raw_records()
    assert calls["n"] == 3


def test_amount_is_rounded_to_cents() -> None:
    result = validate_transactions([{**TXN, "amount": "1234567890.123456"}])
    assert transform_transaction(result.valid_records[0]).amount == Decimal(
        "1234567890.12"
    )


@pytest.mark.parametrize("amount", ["10000000000000000", "9999999999999999.999"])
def test_amount_too_large_for_database_is_rejected(amount: str) -> None:
    result = validate_transactions([{**TXN, "amount": amount}])
    assert result.valid_records == []
    assert "maximum supported value" in result.rejected_records[0].rejection_reasons[0]


def test_non_finite_amount_is_rejected() -> None:
    result = validate_transactions([{**TXN, "amount": "NaN"}])
    assert result.valid_records == []


def test_timezone_aware_dates_are_stored_as_utc(session: Session) -> None:
    record = {**TXN, "transaction_date": "2026-09-24T10:30:00+05:30"}

    run_migration_flow([record], session)

    stored = session.scalar(select(BillingTransaction.transaction_date))
    assert stored == datetime(2026, 9, 24, 5, 0)


def test_flow_can_be_run_repeatedly_on_one_session(session: Session) -> None:
    first = run_migration_flow([TXN], session)
    second = run_migration_flow([TXN, {**TXN, "external_transaction_id": "b"}], session)

    assert first.migration.inserted == 1
    assert second.migration.inserted == 1
    assert second.migration.skipped_duplicates == 1


def test_cli_from_api_runs_pipeline(monkeypatch, tmp_path, capsys) -> None:
    from sqlalchemy.orm import sessionmaker

    from app.database import connection

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(connection, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(connection, "init_db", lambda: None)
    monkeypatch.setattr(
        BillingAPIClient, "fetch_raw_records", lambda self: [TXN], raising=True
    )

    code = cli.main(["--from-api", "--rejected-output", str(tmp_path / "r.json")])

    assert code == 0
    assert '"inserted": 1' in capsys.readouterr().out
    engine.dispose()


def test_cli_returns_2_when_api_fails(monkeypatch) -> None:
    def boom(self):
        raise BillingAPIRequestError("down")

    monkeypatch.setattr(BillingAPIClient, "fetch_raw_records", boom)
    assert cli.main(["--from-api"]) == 2
