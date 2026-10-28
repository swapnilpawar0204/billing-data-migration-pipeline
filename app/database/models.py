from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


def utc_now() -> datetime:
    """Naive UTC timestamp (MySQL DATETIME has no timezone)."""
    return datetime.now(UTC).replace(tzinfo=None)


class BillingTransaction(Base):
    """A billing transaction received from an external source system."""

    __tablename__ = "billing_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    external_transaction_id: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )

    customer_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    invoice_id: Mapped[str | None] = mapped_column(
        String(100), index=True, nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    currency: Mapped[str] = mapped_column(String(10), nullable=False)

    status: Mapped[str] = mapped_column(String(50), index=True, nullable=False)

    transaction_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    source_system: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
