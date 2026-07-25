import uuid
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import String, Enum, DateTime, Date, Index, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AutocountDocument(Base):
    """Synced snapshot of an AutoCount invoice or quotation.

    `contact_id` is left null when `customer_code` doesn't match any
    Contact.autocount_customer_code at sync time — the document still gets
    stored, it just isn't linked to a Contact yet.
    """

    __tablename__ = "autocount_documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    doc_type: Mapped[str] = mapped_column(
        Enum("invoice", "quotation", name="autocount_doc_type"), nullable=False
    )
    doc_no: Mapped[str] = mapped_column(String(50), nullable=False)
    customer_code: Mapped[str] = mapped_column(String(12), nullable=False)
    contact_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="")
    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), nullable=False, default=Decimal("0.00")
    )
    currency_code: Mapped[str] = mapped_column(String(10), nullable=False, default="")
    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Invoice-only: how much of total_amount is still unpaid, and when it's due.
    outstanding_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Quotation-only: AutoCount stores this as free text (e.g. "30 days"), not a date.
    validity: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # [{product_code, description, qty, unit, unit_price, discount_amt, sub_total}, ...]
    line_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_autocount_doc_type_no", "doc_type", "doc_no", unique=True),
        Index("idx_autocount_doc_contact_id", "contact_id"),
        Index("idx_autocount_doc_customer_code", "customer_code"),
    )
