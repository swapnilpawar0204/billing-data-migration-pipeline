from collections.abc import Iterable
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import BillingTransaction
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReconciliationResult:
    expected_count: int
    found_count: int
    missing_count: int
    duplicate_count: int
    reconciled: bool
    missing_external_transaction_ids: list[str] = field(default_factory=list)
    duplicate_external_transaction_ids: list[str] = field(default_factory=list)


def reconcile_transactions(
    session: Session,
    external_transaction_ids: Iterable[str],
) -> ReconciliationResult:
    """Verify that each expected external ID exists exactly once."""
    expected_ids = list(external_transaction_ids)
    expected_set = set(expected_ids)
    logger.info("Reconciliation started for %d expected records", len(expected_ids))

    if not expected_set:
        result = ReconciliationResult(0, 0, 0, 0, True)
        logger.info("Reconciliation completed: reconciled=True")
        return result

    found_ids = set(
        session.scalars(
            select(BillingTransaction.external_transaction_id).where(
                BillingTransaction.external_transaction_id.in_(expected_set)
            )
        )
    )
    missing_ids = sorted(expected_set - found_ids)
    duplicate_rows = session.execute(
        select(
            BillingTransaction.external_transaction_id,
            func.count(BillingTransaction.id),
        )
        .where(BillingTransaction.external_transaction_id.in_(expected_set))
        .group_by(BillingTransaction.external_transaction_id)
        .having(func.count(BillingTransaction.id) > 1)
    ).all()
    duplicate_ids = sorted(row[0] for row in duplicate_rows)
    found_count = sum(expected_ids.count(external_id) for external_id in found_ids)
    duplicate_count = sum(row[1] - 1 for row in duplicate_rows)
    reconciled = (
        found_count == len(expected_ids) and not missing_ids and duplicate_count == 0
    )
    result = ReconciliationResult(
        expected_count=len(expected_ids),
        found_count=found_count,
        missing_count=len(missing_ids),
        duplicate_count=duplicate_count,
        reconciled=reconciled,
        missing_external_transaction_ids=missing_ids,
        duplicate_external_transaction_ids=duplicate_ids,
    )
    logger.info(
        "Reconciliation completed: reconciled=%s missing=%d duplicates=%d",
        result.reconciled,
        result.missing_count,
        result.duplicate_count,
    )
    return result
