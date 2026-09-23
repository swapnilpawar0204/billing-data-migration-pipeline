from datetime import datetime, timezone
from decimal import Decimal

import httpx
import pytest

from app.ingestion.api_client import (
    BillingAPIClient,
    BillingAPIRequestError,
    BillingAPIResponseError,
)

TRANSACTION = {
    "external_transaction_id": "txn-001",
    "customer_id": "customer-001",
    "invoice_id": "invoice-001",
    "amount": "125.50",
    "currency": "USD",
    "status": "paid",
    "transaction_date": "2026-09-23T08:00:00Z",
    "source_system": "billing-api",
}


def test_fetch_transactions_returns_validated_transactions() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/transactions")
        return httpx.Response(200, json={"transactions": [TRANSACTION]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    api_client = BillingAPIClient(client=client)

    transactions = api_client.fetch_transactions()

    assert transactions[0].external_transaction_id == "txn-001"
    assert transactions[0].amount == Decimal("125.50")
    assert transactions[0].transaction_date == datetime(
        2026, 9, 23, 8, 0, tzinfo=timezone.utc
    )
    client.close()


def test_fetch_transactions_raises_for_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    api_client = BillingAPIClient(client=client)

    with pytest.raises(BillingAPIRequestError, match="HTTP 503"):
        api_client.fetch_transactions()

    client.close()


@pytest.mark.parametrize(
    "error",
    [
        httpx.TimeoutException("request timed out"),
        httpx.ConnectError("connection failed"),
    ],
)
def test_fetch_transactions_raises_for_request_failure(
    error: httpx.RequestError,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise error

    client = httpx.Client(transport=httpx.MockTransport(handler))
    api_client = BillingAPIClient(client=client)

    with pytest.raises(BillingAPIRequestError):
        api_client.fetch_transactions()

    client.close()


@pytest.mark.parametrize(
    "payload",
    [
        {"transactions": {"external_transaction_id": "txn-001"}},
        {"transactions": [{"customer_id": "customer-001"}]},
        "not a transaction response",
    ],
)
def test_fetch_transactions_raises_for_malformed_response(payload: object) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    api_client = BillingAPIClient(client=client)

    with pytest.raises(BillingAPIResponseError):
        api_client.fetch_transactions()

    client.close()


def test_fetch_transactions_raises_for_invalid_json() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    api_client = BillingAPIClient(client=client)

    with pytest.raises(BillingAPIResponseError, match="invalid JSON"):
        api_client.fetch_transactions()

    client.close()
