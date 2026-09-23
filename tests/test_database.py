from sqlalchemy import Numeric

from app.database.connection import Base
from app.database.models import BillingTransaction


def test_billing_transaction_model_imports() -> None:
    assert BillingTransaction is not None


def test_billing_transaction_table_metadata() -> None:
    table = BillingTransaction.__table__

    assert table.name == "billing_transactions"
    assert set(table.primary_key.columns.keys()) == {"id"}
    assert {column.name for column in table.columns} == {
        "id",
        "external_transaction_id",
        "customer_id",
        "invoice_id",
        "amount",
        "currency",
        "status",
        "transaction_date",
        "source_system",
        "created_at",
        "updated_at",
    }


def test_billing_transaction_constraints_and_indexes() -> None:
    table = BillingTransaction.__table__
    columns = table.c

    assert columns.external_transaction_id.unique is True
    assert columns.external_transaction_id.index is True
    assert columns.customer_id.index is True
    assert columns.invoice_id.index is True
    assert columns.status.index is True
    assert columns.external_transaction_id.nullable is False
    assert columns.customer_id.nullable is False
    assert columns.invoice_id.nullable is True
    assert columns.amount.nullable is False
    assert columns.currency.nullable is False
    assert columns.status.nullable is False
    assert columns.created_at.nullable is False
    assert columns.updated_at.nullable is False


def test_billing_transaction_amount_is_decimal() -> None:
    amount_type = BillingTransaction.__table__.c.amount.type

    assert isinstance(amount_type, Numeric)
    assert amount_type.precision == 18
    assert amount_type.scale == 2


def test_database_metadata_is_valid() -> None:
    assert "billing_transactions" in Base.metadata.tables
    assert Base.metadata.sorted_tables == [BillingTransaction.__table__]
