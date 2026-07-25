from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel


class LineItem(BaseModel):
    product_code: Optional[str] = None
    description: Optional[str] = None
    qty: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    discount_amt: Optional[float] = None
    sub_total: Optional[float] = None


class AutocountDocumentResponse(BaseModel):
    id: str
    doc_type: str
    doc_no: str
    customer_code: str
    contact_id: Optional[str] = None
    status: str
    total_amount: Decimal
    currency_code: str
    doc_date: Optional[date] = None
    outstanding_amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    validity: Optional[str] = None
    line_items: list[LineItem] = []
    synced_at: datetime

    model_config = {"from_attributes": True}


class SyncResult(BaseModel):
    customers_synced: int
    invoices_synced: int
    invoices_unmatched: int
    quotations_synced: int
    quotations_unmatched: int
    synced_at: datetime
