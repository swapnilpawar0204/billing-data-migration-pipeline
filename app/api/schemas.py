from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from app.ingestion.schemas import BillingTransactionSchema


class TransactionBatchRequest(BaseModel):
    """A batch of raw transaction records awaiting validation."""

    transactions: list[dict[str, Any]] = Field(min_length=0)


class RejectedRecordResponse(BaseModel):
    original_record: Any
    rejection_reasons: list[str]


class ValidationResponse(BaseModel):
    valid_count: int
    valid_records: list[BillingTransactionSchema]
    rejected_count: int
    rejected_records: list[RejectedRecordResponse]


class MigrationCountsResponse(BaseModel):
    received: int
    inserted: int
    skipped_duplicates: int
    failed: int
    failures: list[dict[str, str | None]]


class ReconciliationResponse(BaseModel):
    expected_count: int
    found_count: int
    missing_count: int
    duplicate_count: int
    reconciled: bool
    missing_external_transaction_ids: list[str]
    duplicate_external_transaction_ids: list[str]


class MigrationRunResponse(BaseModel):
    validation: ValidationResponse
    migration: MigrationCountsResponse
    reconciliation: ReconciliationResponse


class TransactionDetailsResponse(BaseModel):
    invoice_id: str | None
    amount: Decimal
    currency: str
    status: str
    transaction_date: datetime | None
    source_system: str | None


class TransactionStatusResponse(BaseModel):
    external_transaction_id: str
    exists: bool
    transaction: TransactionDetailsResponse | None = None
