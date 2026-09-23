from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.connection import Base
from app.database.models import BillingTransaction
from app.ingestion.schemas import BillingTransactionSchema
from app.migration.migration_service import (
    MigrationError,
    migrate_transactions,
    run_migration_flow,
)


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session


def record(external_id: str) -> BillingTransactionSchema:
    return BillingTransactionSchema(
        external_transaction_id=external_id,
        customer_id="customer-001",
        amount=Decimal("10.00"),
        currency="USD",
        status="paid",
    )


def test_successful_insertion(session: Session) -> None:
    result = migrate_transactions([record("txn-001")], session)

    assert result.received == 1
    assert result.inserted == 1
    assert result.skipped_duplicates == 0
    assert session.query(BillingTransaction).count() == 1


def test_multiple_successful_records(session: Session) -> None:
    result = migrate_transactions([record("txn-001"), record("txn-002")], session)

    assert result.inserted == 2
    assert result.migrated_external_transaction_ids == ["txn-001", "txn-002"]


def test_duplicate_external_id_is_skipped(session: Session) -> None:
    migrate_transactions([record("txn-001")], session)

    result = migrate_transactions([record("txn-001"), record("txn-002")], session)

    assert result.inserted == 1
    assert result.skipped_duplicates == 1
    assert session.query(BillingTransaction).count() == 2


def test_failed_migration_rolls_back(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_flush = session.flush
    flush_count = 0

    def failing_flush(*args: object, **kwargs: object) -> None:
        nonlocal flush_count
        flush_count += 1
        if flush_count == 2:
            from sqlalchemy.exc import SQLAlchemyError

            raise SQLAlchemyError("simulated database failure")
        original_flush(*args, **kwargs)

    monkeypatch.setattr(session, "flush", failing_flush)

    with pytest.raises(MigrationError):
        migrate_transactions([record("txn-001"), record("txn-002")], session)

    assert session.query(BillingTransaction).count() == 0


def test_empty_input_returns_structured_result(session: Session) -> None:
    result = migrate_transactions([], session)

    assert result.received == 0
    assert result.inserted == 0
    assert result.failures == []


def test_flow_rejects_invalid_records_and_reconciles(session: Session) -> None:
    raw_records = [
        record("txn-001").model_dump(),
        {**record("txn-002").model_dump(), "amount": "-1.00"},
    ]

    result = run_migration_flow(raw_records, session)

    assert len(result.validation.rejected_records) == 1
    assert result.migration.inserted == 1
    assert result.reconciliation.reconciled is True


def test_flow_transforms_and_skips_duplicate_ids_within_batch(
    session: Session,
) -> None:
    first = record("txn-001").model_dump()
    first["currency"] = " usd "
    first["status"] = " PAID "
    first["invoice_id"] = "   "
    duplicate = record("txn-001").model_dump()

    result = run_migration_flow([first, duplicate], session)

    assert result.transformed_records[0].currency == "USD"
    assert result.transformed_records[0].status == "paid"
    assert result.transformed_records[0].invoice_id is None
    assert result.migration.inserted == 1
    assert result.migration.skipped_duplicates == 1
    assert result.reconciliation.reconciled is True
