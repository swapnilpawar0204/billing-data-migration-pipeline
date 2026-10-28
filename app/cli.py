"""Command-line entry point: run the migration pipeline from a file or the source API.

Examples:
    python -m app.cli --file data/sample_billing_data.json
    python -m app.cli --from-api
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ingestion.api_client import BillingAPIClient, BillingAPIError
from app.migration.migration_service import (
    MigrationError,
    MigrationFlowResult,
    run_migration_flow,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_REJECTED_PATH = Path("data/rejected_records.json")


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load raw records from a JSON file (a list, or {"transactions": [...]})."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("transactions") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise ValueError("JSON must be a list or an object with a 'transactions' list")
    return records


def write_rejected(flow: MigrationFlowResult, path: Path) -> None:
    """Persist rejected records and their reasons for later investigation."""
    if not flow.validation.rejected_records:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    rejected = [
        {"record": r.original_record, "reasons": r.rejection_reasons}
        for r in flow.validation.rejected_records
    ]
    path.write_text(json.dumps(rejected, indent=2, default=str), encoding="utf-8")


def execute(
    records: list[dict[str, Any]],
    session: Session,
    rejected_path: Path = DEFAULT_REJECTED_PATH,
) -> tuple[dict[str, Any], int]:
    """Run the pipeline and return (summary, exit_code)."""
    flow = run_migration_flow(records, session)
    write_rejected(flow, rejected_path)
    summary = {
        "received": flow.migration.received + len(flow.validation.rejected_records),
        "rejected": len(flow.validation.rejected_records),
        "inserted": flow.migration.inserted,
        "skipped_duplicates": flow.migration.skipped_duplicates,
        "reconciled": flow.reconciliation.reconciled,
    }
    return summary, 0 if flow.reconciliation.reconciled else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the billing migration pipeline.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path, help="JSON file with raw transactions")
    source.add_argument(
        "--from-api", action="store_true", help="fetch from the billing API"
    )
    parser.add_argument("--rejected-output", type=Path, default=DEFAULT_REJECTED_PATH)
    args = parser.parse_args(argv)

    # Imported lazily so `--help` works without a database configured.
    from app.database.connection import SessionLocal, init_db

    try:
        if args.from_api:
            with BillingAPIClient() as client:
                records = client.fetch_raw_records()
        else:
            records = load_records(args.file)
    except (BillingAPIError, OSError, ValueError) as exc:
        logger.error("Could not load source records: %s", exc)
        return 2

    try:
        init_db()
        with SessionLocal() as session:
            summary, code = execute(records, session, args.rejected_output)
    except MigrationError as exc:
        logger.error("Migration failed: %s", exc)
        return 2
    except SQLAlchemyError as exc:
        logger.error("Database unavailable: %s", exc.__class__.__name__)
        return 2

    print(json.dumps(summary, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
