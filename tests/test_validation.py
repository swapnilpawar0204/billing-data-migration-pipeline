from decimal import Decimal

import pytest

from app.validation.validators import validate_transactions


def valid_record() -> dict[str, object]:
    return {
        "external_transaction_id": "txn-001",
        "customer_id": "customer-001",
        "invoice_id": "invoice-001",
        "amount": "12.50",
        "currency": "USD",
        "status": "paid",
        "transaction_date": "2026-09-23T08:00:00Z",
        "source_system": "billing-api",
    }


def test_valid_record_is_accepted() -> None:
    result = validate_transactions([valid_record()])

    assert len(result.valid_records) == 1
    assert result.valid_records[0].amount == Decimal("12.50")
    assert result.rejected_records == []


def test_missing_required_field_is_rejected() -> None:
    record = valid_record()
    del record["customer_id"]

    result = validate_transactions([record])

    assert len(result.rejected_records) == 1
    assert any(
        "customer_id" in reason
        for reason in result.rejected_records[0].rejection_reasons
    )


def test_empty_identifier_is_rejected() -> None:
    record = valid_record()
    record["external_transaction_id"] = "   "

    result = validate_transactions([record])

    assert any(
        "external_transaction_id must be non-empty" in reason
        for reason in result.rejected_records[0].rejection_reasons
    )


def test_invalid_amount_is_rejected() -> None:
    record = valid_record()
    record["amount"] = "not-a-number"

    result = validate_transactions([record])

    assert any(
        "amount" in reason for reason in result.rejected_records[0].rejection_reasons
    )


def test_negative_amount_is_rejected() -> None:
    record = valid_record()
    record["amount"] = "-1.00"

    result = validate_transactions([record])

    assert "amount must be non-negative" in result.rejected_records[0].rejection_reasons


def test_missing_currency_is_rejected() -> None:
    record = valid_record()
    record["currency"] = ""

    result = validate_transactions([record])

    assert "currency must be non-empty" in result.rejected_records[0].rejection_reasons


def test_multiple_validation_failures_are_retained() -> None:
    record = valid_record()
    record["external_transaction_id"] = ""
    record["customer_id"] = " "
    record["amount"] = "-2.00"
    record["currency"] = ""
    record["status"] = ""

    result = validate_transactions([record])
    reasons = result.rejected_records[0].rejection_reasons

    assert len(reasons) >= 5
    assert result.rejected_records[0].original_record == record


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("transaction_date", "not-a-date"),
        ("external_transaction_id", None),
        ("customer_id", None),
        ("currency", None),
        ("status", None),
    ],
)
def test_invalid_or_missing_fields_are_rejected(field_name: str, value: object) -> None:
    record = valid_record()
    if value is None:
        del record[field_name]
    else:
        record[field_name] = value

    result = validate_transactions([record])

    assert len(result.valid_records) == 0
    assert len(result.rejected_records) == 1
    assert any(
        field_name in reason for reason in result.rejected_records[0].rejection_reasons
    )


@pytest.mark.parametrize("amount", ["0", "9999999999999999.99", "1234567890.123456"])
def test_supported_non_negative_decimal_amounts_are_accepted(
    amount: str,
) -> None:
    record = valid_record()
    record["amount"] = amount

    result = validate_transactions([record])

    assert len(result.valid_records) == 1
