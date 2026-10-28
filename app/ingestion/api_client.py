import time
from collections.abc import Callable
from typing import Any, Self

import httpx
from pydantic import ValidationError

from app.config.settings import settings
from app.ingestion.schemas import BillingTransactionSchema
from app.utils.logger import get_logger

logger = get_logger(__name__)

_BACKOFF_BASE_SECONDS = 0.5


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
            timeout=httpx.Timeout(settings.api_timeout_seconds),
            headers=self._build_headers(),
        )
        self._transactions_url = f"{settings.api_base_url.rstrip('/')}/transactions"

    @staticmethod
    def _build_headers() -> dict[str, str]:
        if settings.api_key:
            return {"Authorization": f"Bearer {settings.api_key}"}
        return {}

    def _get_with_retries(self) -> httpx.Response:
        """GET the transactions URL, retrying transient failures with backoff.

        Timeouts, connection errors and HTTP 429/5xx are retried up to
        ``settings.api_max_retries`` times (exponential backoff). Other 4xx
        responses are permanent and fail immediately.
        """
        attempts = settings.api_max_retries + 1
        for attempt in range(1, attempts + 1):
            try:
                response = self._client.get(self._transactions_url)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                code = exc.response.status_code
                transient = code == 429 or code >= 500
                logger.error("Billing API returned HTTP status %s", code)
                if not transient or attempt == attempts:
                    raise BillingAPIRequestError(
                        f"Billing API returned HTTP {code}"
                    ) from exc
            except httpx.TimeoutException as exc:
                logger.error("Billing API request timed out")
                if attempt == attempts:
                    raise BillingAPIRequestError(
                        "Billing API request timed out"
                    ) from exc
            except httpx.RequestError as exc:
                logger.error("Billing API request failed: %s", exc.__class__.__name__)
                if attempt == attempts:
                    raise BillingAPIRequestError("Billing API request failed") from exc

            delay = _BACKOFF_BASE_SECONDS * 2 ** (attempt - 1)
            logger.warning(
                "Retrying billing API request in %.1fs (attempt %d/%d)",
                delay,
                attempt,
                attempts,
            )
            time.sleep(delay)
        raise AssertionError("unreachable")  # pragma: no cover

    def fetch_raw_records(self) -> list[dict[str, Any]]:
        """Fetch the raw (unvalidated) transaction records from the billing API.

        Validation is deliberately left to the pipeline so that bad records are
        rejected and reported individually instead of failing the whole fetch.
        """
        logger.info("Fetching billing transactions from external API")
        response = self._get_with_retries()

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
        return records

    def fetch_transactions(self) -> list[BillingTransactionSchema]:
        """Fetch and strictly validate all transactions returned by the API."""
        records = self.fetch_raw_records()
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
