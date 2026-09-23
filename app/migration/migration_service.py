from collections.abc import Iterable
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models import BillingTransaction
from app.ingestion.schemas import BillingTransactionSchema
from app.reconciliation.reconciliation_service import (
    ReconciliationResult,
    reconcile_transactions,
)
from app.transformation.transformer import transform_transactions
from app.utils.logger import get_logger
from app.validation.validators import ValidationResult, validate_transactions

logger = get_logger(__name__)


@dataclass(frozen=True)
class MigrationFailure:
    external_transaction_id: str | None
    reason: str


@dataclass
class MigrationResult:
    received: int
    inserted: int = 0
    skipped_duplicates: int = 0
    failed: int = 0
    failures: list[MigrationFailure] = field(default_factory=list)
    migrated_external_transaction_ids: list[str] = field(default_factory=list)


class MigrationError(RuntimeError):
    """Raised when an atomic migration cannot be completed."""

    def __init__(
        self,
        message: str,
        failures: list[MigrationFailure],
        result: MigrationResult,
    ) -> None:
        super().__init__(message)
        self.failures = failures
        self.result = result


def _to_model(record: BillingTransactionSchema) -> BillingTransaction:
    return BillingTransaction(**record.model_dump())


def migrate_transactions(
    records: Iterable[BillingTransactionSchema],
    session: Session,
) -> MigrationResult:
    """Insert transactions atomically, skipping existing external IDs.

    Duplicate handling is idempotent: records already present in the database,
    and repeated IDs within the same batch, are counted and skipped.
    """
    records = list(records)
    result = MigrationResult(received=len(records))
    logger.info("Migration started for %d records", result.received)

    current_external_id: str | None = None
    try:
        with session.begin():
            existing_ids = set(
                session.scalars(
                    select(BillingTransaction.external_transaction_id).where(
                        BillingTransaction.external_transaction_id.in_(
                            [record.external_transaction_id for record in records]
                        )
                    )
                )
            )
            seen_ids = set(existing_ids)

            for record in records:
                external_id = record.external_transaction_id
                current_external_id = external_id
                if external_id in seen_ids:
                    result.skipped_duplicates += 1
                    result.migrated_external_transaction_ids.append(external_id)
                    continue

                session.add(_to_model(record))
                session.flush()
                seen_ids.add(external_id)
                result.inserted += 1
                result.migrated_external_transaction_ids.append(external_id)
    except SQLAlchemyError as exc:
        session.rollback()
        failure = MigrationFailure(
            external_transaction_id=current_external_id,
            reason="database migration failed; transaction rolled back",
        )
        result.failed = result.received - result.skipped_duplicates
        result.failures.append(failure)
        logger.error("Migration failed and was rolled back")
        raise MigrationError(str(failure.reason), result.failures, result) from exc

    logger.info(
        "Migration completed: inserted=%d skipped_duplicates=%d failed=%d",
        result.inserted,
        result.skipped_duplicates,
        result.failed,
    )
    return result


@dataclass
class MigrationFlowResult:
    validation: ValidationResult
    transformed_records: list[BillingTransactionSchema]
    migration: MigrationResult
    reconciliation: ReconciliationResult


def run_migration_flow(
    raw_records: Iterable[BillingTransactionSchema | dict[str, object]],
    session: Session,
) -> MigrationFlowResult:
    """Run validation, transformation, migration, and reconciliation in order."""
    validation = validate_transactions(raw_records)
    transformed = transform_transactions(validation.valid_records)
    migration = migrate_transactions(transformed, session)
    reconciliation = reconcile_transactions(
        session,
        migration.migrated_external_transaction_ids,
    )
    return MigrationFlowResult(
        validation=validation,
        transformed_records=transformed,
        migration=migration,
        reconciliation=reconciliation,
    )
