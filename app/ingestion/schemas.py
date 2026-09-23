from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BillingTransactionSchema(BaseModel):
    """Validated transaction data received from the billing API."""

    external_transaction_id: str
    customer_id: str
    invoice_id: str | None = None
    amount: Decimal
    currency: str
    status: str
    transaction_date: datetime | None = None
    source_system: str | None = None
