from decimal import Decimal

from app.ingestion.schemas import BillingTransactionSchema
from app.transformation.transformer import (
    transform_transaction,
    transform_transactions,
)


def valid_record() -> BillingTransactionSchema:
    return BillingTransactionSchema(
        external_transaction_id=" txn-001 ",
        customer_id=" customer-001 ",
        invoice_id="   ",
        amount=Decimal("12.50"),
        currency=" usd ",
        status=" Paid ",
        transaction_date="2026-09-23T08:00:00Z",
        source_system="  ",
    )


def test_transformation_cleans_whitespace_and_normalizes_values() -> None:
    transformed = transform_transaction(valid_record())

    assert transformed.external_transaction_id == "txn-001"
    assert transformed.customer_id == "customer-001"
    assert transformed.currency == "USD"
    assert transformed.status == "paid"
    assert transformed.invoice_id is None
    assert transformed.source_system is None


def test_transformation_preserves_money_dates_and_ids() -> None:
    source = valid_record()

    transformed = transform_transaction(source)

    assert transformed.amount == Decimal("12.50")
    assert transformed.transaction_date == source.transaction_date
    assert transformed.external_transaction_id == "txn-001"


def test_transform_transactions_handles_a_batch() -> None:
    transformed = transform_transactions([valid_record(), valid_record()])

    assert len(transformed) == 2
    assert all(record.currency == "USD" for record in transformed)
