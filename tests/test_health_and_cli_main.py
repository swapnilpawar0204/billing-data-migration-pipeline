import pytest
from sqlalchemy.exc import OperationalError

from app import cli
from app.monitoring import health
from app.validation.validators import validate_transactions


def test_check_database_true(monkeypatch) -> None:
    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, *_a):
            return 1

    monkeypatch.setattr(health.engine, "connect", lambda: Conn())
    assert health.check_database() is True


def test_check_database_false_on_error(monkeypatch) -> None:
    def boom():
        raise OperationalError("SELECT 1", {}, Exception("down"))

    monkeypatch.setattr(health.engine, "connect", boom)
    assert health.check_database() is False


def test_non_mapping_record_is_rejected() -> None:
    result = validate_transactions(["not-a-dict", 42])  # type: ignore[list-item]
    assert len(result.rejected_records) == 2
    assert result.rejected_records[0].rejection_reasons == ["record must be a mapping"]


def test_cli_main_returns_2_for_missing_file(tmp_path) -> None:
    assert cli.main(["--file", str(tmp_path / "missing.json")]) == 2


def test_cli_main_requires_a_source() -> None:
    with pytest.raises(SystemExit):
        cli.main([])


def test_cli_main_runs_end_to_end(monkeypatch, tmp_path, capsys) -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import connection
    from app.database.connection import Base

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(connection, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(connection, "init_db", lambda: None)

    code = cli.main(
        [
            "--file",
            "data/sample_billing_data.json",
            "--rejected-output",
            str(tmp_path / "rej.json"),
        ]
    )

    assert code == 0
    assert '"reconciled": true' in capsys.readouterr().out
    engine.dispose()
