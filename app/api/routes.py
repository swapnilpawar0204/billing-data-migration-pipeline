from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.schemas import (
    MigrationCountsResponse,
    MigrationRunResponse,
    ReconciliationResponse,
    RejectedRecordResponse,
    TransactionBatchRequest,
    TransactionDetailsResponse,
    TransactionStatusResponse,
    ValidationResponse,
)
from app.config.settings import settings
from app.database.connection import get_db
from app.database.models import BillingTransaction
from app.migration.migration_service import (
    MigrationError,
    run_migration_flow,
)
from app.transformation.transformer import transform_transactions
from app.validation.validators import ValidationResult, validate_transactions

router = APIRouter()
migration_router = APIRouter(prefix="/api/v1/migration", tags=["migration"])
db_session_dependency = Depends(get_db)


def _validation_response(
    validation: ValidationResult, transformed: list
) -> ValidationResponse:
    return ValidationResponse(
        valid_count=len(transformed),
        valid_records=transformed,
        rejected_count=len(validation.rejected_records),
        rejected_records=[
            RejectedRecordResponse(
                original_record=record.original_record,
                rejection_reasons=record.rejection_reasons,
            )
            for record in validation.rejected_records
        ],
    )


@router.get("/health", summary="Check application health")
async def health_check() -> dict[str, str]:
    """Return the application health status for Phase 2."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }


@migration_router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Validate and transform billing transactions",
)
def validate_migration_batch(payload: TransactionBatchRequest) -> ValidationResponse:
    """Validate and transform a batch without writing to the database."""
    validation = validate_transactions(payload.transactions)
    transformed = transform_transactions(validation.valid_records)
    return _validation_response(validation, transformed)


@migration_router.post(
    "/run",
    response_model=MigrationRunResponse,
    summary="Run migration and reconciliation",
)
def run_migration_batch(
    payload: TransactionBatchRequest,
    session: Session = db_session_dependency,
) -> MigrationRunResponse:
    """Validate, transform, migrate, and reconcile a transaction batch."""
    try:
        flow = run_migration_flow(payload.transactions, session)
    except MigrationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Migration could not be completed",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable",
        ) from exc

    migration = flow.migration
    return MigrationRunResponse(
        validation=_validation_response(flow.validation, flow.transformed_records),
        migration=MigrationCountsResponse(
            received=migration.received,
            inserted=migration.inserted,
            skipped_duplicates=migration.skipped_duplicates,
            failed=migration.failed,
            failures=[
                {
                    "external_transaction_id": failure.external_transaction_id,
                    "reason": failure.reason,
                }
                for failure in migration.failures
            ],
        ),
        reconciliation=ReconciliationResponse(
            **flow.reconciliation.__dict__,
        ),
    )


@migration_router.get(
    "/status/{external_transaction_id}",
    response_model=TransactionStatusResponse,
    summary="Check migration status for a transaction",
)
def migration_status(
    external_transaction_id: str,
    session: Session = db_session_dependency,
) -> TransactionStatusResponse:
    """Return safe target status information for an external transaction ID."""
    transaction = session.scalar(
        select(BillingTransaction).where(
            BillingTransaction.external_transaction_id == external_transaction_id
        )
    )
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return TransactionStatusResponse(
        external_transaction_id=external_transaction_id,
        exists=True,
        transaction=TransactionDetailsResponse(
            invoice_id=transaction.invoice_id,
            amount=transaction.amount,
            currency=transaction.currency,
            status=transaction.status,
            transaction_date=transaction.transaction_date,
            source_system=transaction.source_system,
        ),
    )


router.include_router(migration_router)
