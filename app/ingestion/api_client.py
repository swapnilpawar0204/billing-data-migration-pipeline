from collections.abc import Callable
from typing import Any, Self

import httpx
from pydantic import ValidationError

from app.config.settings import settings
from app.ingestion.schemas import BillingTransactionSchema
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BillingAPIError(RuntimeError):
    """Base exception for billing API client failures."""


class BillingAPIRequestError(BillingAPIError):
    """Raised when a billing API request cannot be completed."""


class BillingAPIResponseError(BillingAPIError):
    """Raised when a billing API response is invalid or unexpected."""


class BillingAPIClient:
    """Client for retrieving transactions from the external billing API."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        client_factory: Callable[..., httpx.Client] = httpx.Client,
    ) -> None:
        self._owns_client = client is None
        self._client = client or client_factory(
            timeout=httpx.Timeout(10.0),
            headers=self._build_headers(),
        )
        self._transactions_url = f"{settings.api_base_url.rstrip('/')}/transactions"

    @staticmethod
    def _build_headers() -> dict[str, str]:
        if settings.api_key:
            return {"Authorization": f"Bearer {settings.api_key}"}
        return {}

    def fetch_transactions(self) -> list[BillingTransactionSchema]:
        """Fetch and validate all transactions returned by the billing API."""
        logger.info("Fetching billing transactions from external API")

        try:
            response = self._client.get(self._transactions_url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.error("Billing API request timed out")
            raise BillingAPIRequestError("Billing API request timed out") from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Billing API returned HTTP status %s", exc.response.status_code
            )
            raise BillingAPIRequestError(
                f"Billing API returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Billing API request failed: %s", exc.__class__.__name__)
            raise BillingAPIRequestError("Billing API request failed") from exc

        try:
            payload: Any = response.json()
        except ValueError as exc:
            logger.error("Billing API returned invalid JSON")
            raise BillingAPIResponseError("Billing API returned invalid JSON") from exc

        records = payload.get("transactions") if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            logger.error("Billing API returned an unexpected response structure")
            raise BillingAPIResponseError(
                "Billing API response must be a list or contain a transactions list"
            )

        try:
            return [
                BillingTransactionSchema.model_validate(record) for record in records
            ]
        except (TypeError, ValidationError) as exc:
            logger.error("Billing API returned invalid transaction data")
            raise BillingAPIResponseError(
                "Billing API returned invalid transaction data"
            ) from exc

    def close(self) -> None:
        """Close the underlying HTTP client when it is owned by this instance."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
