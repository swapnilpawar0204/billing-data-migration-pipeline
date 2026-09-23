from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.connection import Base
from app.ingestion.schemas import BillingTransactionSchema
from app.migration.migration_service import migrate_transactions
from app.reconciliation.reconciliation_service import reconcile_transactions


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


def test_complete_reconciliation(session: Session) -> None:
    migrate_transactions([record("txn-001"), record("txn-002")], session)

    result = reconcile_transactions(session, ["txn-001", "txn-002"])

    assert result.reconciled is True
    assert result.expected_count == 2
    assert result.found_count == 2
    assert result.missing_count == 0


def test_missing_database_record(session: Session) -> None:
    migrate_transactions([record("txn-001")], session)

    result = reconcile_transactions(session, ["txn-001", "txn-002"])

    assert result.reconciled is False
    assert result.missing_external_transaction_ids == ["txn-002"]
    assert result.missing_count == 1


def test_count_mismatch_is_not_reconciled(session: Session) -> None:
    migrate_transactions([record("txn-001")], session)

    result = reconcile_transactions(session, ["txn-001", "txn-001", "txn-002"])

    assert result.reconciled is False
    assert result.expected_count == 3
    assert result.found_count == 2


def test_empty_reconciliation_is_successful(session: Session) -> None:
    result = reconcile_transactions(session, [])

    assert result.reconciled is True
    assert result.expected_count == 0


def test_empty_database_is_not_reconciled_for_expected_records(
    session: Session,
) -> None:
    result = reconcile_transactions(session, ["txn-001", "txn-002"])

    assert result.reconciled is False
    assert result.found_count == 0
    assert result.missing_count == 2


def test_mixed_existing_and_missing_records(session: Session) -> None:
    migrate_transactions([record("txn-001")], session)

    result = reconcile_transactions(session, ["txn-001", "txn-002", "txn-003"])

    assert result.reconciled is False
    assert result.found_count == 1
    assert result.missing_external_transaction_ids == ["txn-002", "txn-003"]
