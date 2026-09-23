from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from app.ingestion.schemas import BillingTransactionSchema


class RejectedRecord(BaseModel):
    """A source record that could not be accepted for transformation."""

    original_record: Any
    rejection_reasons: list[str]


class ValidationResult(BaseModel):
    """The accepted and rejected results of validating source records."""

    valid_records: list[BillingTransactionSchema]
    rejected_records: list[RejectedRecord]


def _record_mapping(record: Any) -> Mapping[str, Any] | None:
    if isinstance(record, BillingTransactionSchema):
        return record.model_dump()
    if isinstance(record, Mapping):
        return record
    return None


def _pydantic_reasons(error: ValidationError) -> list[str]:
    reasons: list[str] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        reasons.append(f"{location}: {item['msg']}")
    return reasons


def validate_transactions(
    records: Iterable[BillingTransactionSchema | Mapping[str, Any]],
) -> ValidationResult:
    """Validate records while retaining every rejected record and its reasons."""
    valid_records: list[BillingTransactionSchema] = []
    rejected_records: list[RejectedRecord] = []

    for source_record in records:
        record = _record_mapping(source_record)
        if record is None:
            rejected_records.append(
                RejectedRecord(
                    original_record=source_record,
                    rejection_reasons=["record must be a mapping"],
                )
            )
            continue

        reasons: list[str] = []
        try:
            validated = BillingTransactionSchema.model_validate(record)
        except ValidationError as error:
            reasons.extend(_pydantic_reasons(error))
            validated = None

        for field_name in ("external_transaction_id", "customer_id"):
            value = record.get(field_name)
            if isinstance(value, str) and not value.strip():
                reasons.append(f"{field_name} must be non-empty")

        for field_name in ("currency", "status"):
            value = record.get(field_name)
            if isinstance(value, str) and not value.strip():
                reasons.append(f"{field_name} must be non-empty")

        if validated is not None:
            if not validated.amount.is_finite():
                reasons.append("amount must be finite")
            elif validated.amount < 0:
                reasons.append("amount must be non-negative")

        if reasons:
            rejected_records.append(
                RejectedRecord(
                    original_record=source_record,
                    rejection_reasons=list(dict.fromkeys(reasons)),
                )
            )
        elif validated is not None:
            valid_records.append(validated)

    return ValidationResult(
        valid_records=valid_records,
        rejected_records=rejected_records,
    )
