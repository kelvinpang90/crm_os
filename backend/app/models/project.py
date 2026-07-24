import uuid
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, Index, JSON, Text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

_LongText = Text().with_variant(mysql.LONGTEXT(), "mysql")


class Project(Base):
    """A roofing project tracked through the 12-step workflow.

    Self-contained module: no foreign keys to the CRM core. The project manager
    is stored as a plain name string to keep the data independent.
    """

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    service_type: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    project_manager: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    current_step: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Warranty confirmation (step 12 gate): captured once when the project first
    # advances into warranty_active, then read-only. Nullable for projects that
    # reached step 12 before this feature existed (no backfill).
    satisfaction_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    signature_data: Mapped[str | None] = mapped_column(_LongText, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("idx_project_manager", "project_manager"),
        Index("idx_project_deleted_at", "deleted_at"),
    )


class ProjectStepHistory(Base):
    """Audit trail: one row each time a project enters a step."""

    __tablename__ = "project_step_history"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    step_no: Mapped[int] = mapped_column(Integer, nullable=False)
    entered_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_by: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    photos: Mapped[list | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("idx_step_project_id", "project_id"),
    )
