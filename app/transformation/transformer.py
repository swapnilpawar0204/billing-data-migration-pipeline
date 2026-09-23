from collections.abc import Iterable

from app.ingestion.schemas import BillingTransactionSchema


def transform_transaction(
    record: BillingTransactionSchema,
) -> BillingTransactionSchema:
    """Normalize one already-validated billing transaction deterministically."""
    values = record.model_dump()
    for field_name in (
        "external_transaction_id",
        "customer_id",
        "currency",
        "status",
    ):
        values[field_name] = values[field_name].strip()

    values["currency"] = values["currency"].upper()
    values["status"] = values["status"].lower()

    for field_name in ("invoice_id", "source_system"):
        if values[field_name] is not None:
            values[field_name] = values[field_name].strip() or None

    return BillingTransactionSchema.model_validate(values)


def transform_transactions(
    records: Iterable[BillingTransactionSchema],
) -> list[BillingTransactionSchema]:
    """Normalize all validated billing transactions without changing their meaning."""
    return [transform_transaction(record) for record in records]
