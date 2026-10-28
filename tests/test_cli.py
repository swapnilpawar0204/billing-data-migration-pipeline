import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.cli import execute, load_records
from app.database.connection import Base
from app.database.models import BillingTransaction

SAMPLE = Path(__file__).parents[1] / "data" / "sample_billing_data.json"


@pytest.fixture
def session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
    engine.dispose()


def test_sample_data_loads() -> None:
    assert len(load_records(SAMPLE)) == 6


def test_sample_data_migrates_and_reports_rejections(session, tmp_path) -> None:
    rejected_path = tmp_path / "rejected.json"

    summary, code = execute(load_records(SAMPLE), session, rejected_path)

    assert code == 0
    assert summary["reconciled"] is True
    assert summary["rejected"] == 2
    assert summary["inserted"] == 3
    assert summary["skipped_duplicates"] == 1
    assert session.scalar(select(func.count(BillingTransaction.id))) == 3
    rejected = json.loads(rejected_path.read_text())
    assert len(rejected) == 2
    assert all(item["reasons"] for item in rejected)


def test_rerun_is_idempotent(session, tmp_path) -> None:
    records = load_records(SAMPLE)
    execute(records, session, tmp_path / "r.json")
    summary, code = execute(records, session, tmp_path / "r.json")

    assert code == 0
    assert summary["inserted"] == 0
    assert session.scalar(select(func.count(BillingTransaction.id))) == 3


def test_load_records_rejects_bad_shape(tmp_path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"foo": 1}')
    with pytest.raises(ValueError):
        load_records(bad)
